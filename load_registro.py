import os
import argparse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
from azure.data.tables import TableServiceClient, TableClient
from dotenv import load_dotenv
import openpyxl
import json

# Carregar variáveis do arquivo .env
load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch records from Azure Table Storage based on filters"
    )
    parser.add_argument(
        "--connection_string",
        help="Azure storage connection string",
        default=os.getenv("AZURE_TABLE_CONNECTION_STRING"),
    )
    parser.add_argument(
        "--table_name",
        help="Azure table name",
        default=os.getenv("AZURE_TABLE_NAME", "RegistrosTabela"),
    )
    parser.add_argument("--start_date", help="Start date (DD/MM/YYYY)", required=True)
    parser.add_argument("--end_date", help="End date (DD/MM/YYYY)", required=True)
    parser.add_argument(
        "--matricula", help="Registration number (PartitionKey)", required=True
    )
    parser.add_argument("--output", help="Output file path", default="registros.xlsx")
    return parser.parse_args()


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
            print(
                f"Error fetching record for matricula {matricula}, date {row_key}: {e}"
            )

    return results


def main():
    args = parse_args()

    # Validate connection string
    if not args.connection_string:
        print("Error: Azure Storage connection string not provided.")
        print(
            "Ensure AZURE_TABLE_CONNECTION_STRING is set in the .env file or provide --connection_string argument."
        )
        return

    # Get all months between start and end date
    date_range = get_date_range(args.start_date, args.end_date)

    # Fetch records from Azure Table
    results = query_table(
        args.connection_string, args.table_name, args.matricula, date_range
    )

    if not results:
        print(
            f"No records found for matricula {args.matricula} in the specified date range."
        )
        return

    folha_de_pagamento = {}

    resumo = {
        "matricula": args.matricula,
        "data_inicio": args.start_date,
        "data_fim": args.end_date,
        "nome": "",
        "data_admissao": "",
    }
    
    # Process each record
    for record in results:
        dict_record = dict(record)
        # print(json.loads(dict_record["dados_json"])["unidadeGestora"])
        # continue
        record_data = json.loads(dict_record["dados_json"])
        if resumo["nome"] == "":
            resumo["nome"] = record_data["matricula"]["nome"]
        if resumo["data_admissao"] == "":
            resumo["data_admissao"] = record_data["matricula"]["dataAdmissao"]
        for dados in record_data["listFolha"]:
            # print(dados)
            # continue
            data = dados["data"]
            divisor = dados["historico"]["nrHorasMensais"]
            tipo_calculo = dados["tipoCalculo"]["tipoDenominacao"]
            for evento in dados["listEventos"]:
                # print(evento)
                # continue
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
    
    print(folha_de_pagamento)
    
    # Create a summary DataFrame first
    summary_data = []
    for key, value in folha_de_pagamento.items():
        df_temp = pd.DataFrame(value)
        summary_data.append({
            'Evento': key,
            'Total de Registros': len(df_temp),
            'Valor Total': df_temp['valor'].sum(),
            'Período': f"{args.start_date} até {args.end_date}",
            'Matrícula': args.matricula,
            'Nome': resumo["nome"],
            'Data de Admissão': resumo["data_admissao"],
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Create Excel file with summary as first sheet
    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        # Write the summary sheet first
        summary_df.to_excel(writer, sheet_name='Resumo', index=False)
        print(f"Summary saved to {args.output} in sheet Resumo")
        
        # Then write each event to its own sheet
        for key, value in folha_de_pagamento.items():
            df = pd.DataFrame(value)
            # Replace invalid characters in sheet names
            valid_sheet_name = key.replace('/', '_').replace('\\', '_').replace('?', '_').replace('*', '_').replace('[', '_').replace(']', '_').replace(':', '_')
            # Truncate sheet name if too long (Excel limit is 31 characters)
            valid_sheet_name = valid_sheet_name[:31]
            # Save each DataFrame to a different sheet
            df.to_excel(writer, sheet_name=valid_sheet_name, index=False)
            print(f"Records saved to {args.output} in sheet {valid_sheet_name}")
            
    # # Convert results to DataFrame

            
    # # Save to Excel file
    # output_file = args.output
    # if output_file.endswith(".xlsx"):
    #     df.to_excel(output_file, index=False)
    # else:
    #     df.to_csv(output_file, index=False)
    # print(f"Records saved to {output_file}")
    



    # # Convert results to DataFrame
    # df = pd.DataFrame(results)

    # # Save to file
    # df.to_csv(args.output, index=False)
    # print(f"Records saved to {args.output}")


if __name__ == "__main__":
    main()
