import logging
import azure.functions as func
import json
import os
import tempfile
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from azure.data.tables import TableServiceClient, TableClient
from dotenv import load_dotenv
import io
import base64

# Carregar variáveis do arquivo .env
load_dotenv()

def get_date_range(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    end_date = datetime.strptime(end_date_str, "%d/%m/%Y")

    # Generate all months between start_date and end_date
    current_date = start_date.replace(day=1)
    date_list = []

    while current_date <= end_date:
        month_year = current_date.strftime("%m_%Y")
        date_list.append(month_year)
        current_date += relativedelta(months=1)

    return date_list

def query_table(connection_string, table_name, matricula, row_keys):
    results = []

    # Connect to the table service
    table_service = TableServiceClient.from_connection_string(connection_string)
    table_client = table_service.get_table_client(table_name)

    for row_key in row_keys:
        try:
            # Query with PartitionKey and RowKey
            entity = table_client.get_entity(partition_key=matricula, row_key=row_key)
            results.append(entity)
        except Exception as e:
            logging.error(f"Error fetching record for matricula {matricula}, date {row_key}: {e}")

    return results

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processando requisição HTTP.')

    # Verificar se é uma requisição OPTIONS (preflight)
    if req.method.lower() == 'options':
        return func.HttpResponse(
            status_code=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '86400'  # 24 horas em segundos
            }
        )

    # Obter parâmetros da requisição
    try:
        matricula = req.params.get('matricula')
        start_date = req.params.get('start_date')
        end_date = req.params.get('end_date')
        
        # Verificar se todos os parâmetros foram fornecidos
        if not all([matricula, start_date, end_date]):
            req_body = req.get_json()
            matricula = req_body.get('matricula')
            start_date = req_body.get('start_date')
            end_date = req_body.get('end_date')
    except ValueError:
        return func.HttpResponse(
             "Erro ao ler parâmetros da requisição.",
             status_code=400
        )

    # Validar parâmetros obrigatórios
    if not all([matricula, start_date, end_date]):
        return func.HttpResponse(
             "Por favor, forneça os parâmetros: matricula, start_date e end_date.",
             status_code=400
        )
    
    # Obter a connection string e nome da tabela
    connection_string = os.getenv("AZURE_TABLE_CONNECTION_STRING")
    table_name = os.getenv("AZURE_TABLE_NAME", "RegistrosTabela")
    
    if not connection_string:
        return func.HttpResponse(
             "Erro: Azure Storage connection string não configurada.",
             status_code=500
        )

    # Obter o intervalo de datas
    date_range = get_date_range(start_date, end_date)

    # Consultar registros no Azure Table
    results = query_table(connection_string, table_name, matricula, date_range)

    if not results:
        return func.HttpResponse(
            f"Nenhum registro encontrado para a matrícula {matricula} no período especificado.",
            status_code=404
        )

    folha_de_pagamento = {}
    resumo = {
        "matricula": matricula,
        "data_inicio": start_date,
        "data_fim": end_date,
        "nome": "",
        "data_admissao": "",
    }
    
    # Processar cada registro
    for record in results:
        dict_record = dict(record)
        record_data = json.loads(dict_record["dados_json"])
        if resumo["nome"] == "":
            resumo["nome"] = record_data["matricula"]["nome"]
        if resumo["data_admissao"] == "":
            resumo["data_admissao"] = record_data["matricula"]["dataAdmissao"]
        for dados in record_data["listFolha"]:
            data = dados["data"]
            divisor = dados["historico"]["nrHorasMensais"]
            tipo_calculo = dados["tipoCalculo"]["tipoDenominacao"]
            for evento in dados["listEventos"]:
                if evento["denominacao"] not in folha_de_pagamento:
                    folha_de_pagamento[evento["denominacao"]] = []
                folha_de_pagamento[evento["denominacao"]].append(
                    {
                        "data": data,
                        "referência": evento["valorReferencia"],
                        "valor": (
                            evento["valorEvento"]
                            if evento["tipoEventoDenominacao"] == "Provento"
                            else -evento["valorEvento"]
                        ),
                        "divisor": divisor,
                        "tipo_calculo": tipo_calculo,
                    }
                )
    
    # Criar DataFrame resumo
    summary_data = []
    for key, value in folha_de_pagamento.items():
        df_temp = pd.DataFrame(value)
        summary_data.append({
            'Evento': key,
            'Total de Registros': len(df_temp),
            'Valor Total': df_temp['valor'].sum(),
            'Período': f"{start_date} até {end_date}",
            'Matrícula': matricula,
            'Nome': resumo["nome"],
            'Data de Admissão': resumo["data_admissao"],
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Criar arquivo Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Escrever a planilha de resumo primeiro
        summary_df.to_excel(writer, sheet_name='Resumo', index=False)
        
        # Escrever cada evento em sua própria planilha
        for key, value in folha_de_pagamento.items():
            df = pd.DataFrame(value)
            # Substituir caracteres inválidos nos nomes das planilhas
            valid_sheet_name = key.replace('/', '_').replace('\\', '_').replace('?', '_').replace('*', '_').replace('[', '_').replace(']', '_').replace(':', '_')
            # Truncar nome da planilha se muito longo (limite do Excel é 31 caracteres)
            valid_sheet_name = valid_sheet_name[:31]
            # Salvar cada DataFrame em uma planilha diferente
            df.to_excel(writer, sheet_name=valid_sheet_name, index=False)
    
    # Configurar a resposta HTTP com o arquivo Excel
    output.seek(0)
    
    # Nome do arquivo de saída
    file_name = f"registros_matricula_{matricula}_{start_date.replace('/', '-')}_a_{end_date.replace('/', '-')}.xlsx"
    
    # Retornar o arquivo como resposta HTTP com cabeçalhos CORS
    return func.HttpResponse(
        body=output.getvalue(),
        status_code=200,
        headers={
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
    )
