import curl_cffi.requests as requests
import time
from datetime import datetime
import os
import json

def formatar_data(mes, ano):
    """Formata o mês e ano para o formato mm/aaaa requerido pela API."""
    return f"{mes:02d}/{ano}"

def criar_intervalo_datas(data_inicio, data_fim):
    """Cria uma lista de strings no formato mm/aaaa para um intervalo de datas."""
    inicio = datetime.strptime(data_inicio, "%m/%Y")
    fim = datetime.strptime(data_fim, "%m/%Y")
    
    datas = []
    data_atual = inicio
    
    while data_atual <= fim:
        datas.append(data_atual.strftime("%m/%Y"))
        # Avança para o próximo mês
        if data_atual.month == 12:
            data_atual = data_atual.replace(year=data_atual.year + 1, month=1)
        else:
            data_atual = data_atual.replace(month=data_atual.month + 1)
    
    return datas

def obter_dados_pessoal(referencia, codigo_unidade=0):
    """
    Obtém dados da API de pessoal da prefeitura de Itajaí.
    
    Parâmetros:
        referencia (str): Data de referência no formato "mm/aaaa"
        codigo_unidade (int): Código da unidade (0 para todas)
    
    Retorna:
        dict: Dados obtidos da API ou None em caso de erro
    """
    url = "https://portaltransparencia.itajai.sc.gov.br:443/epublica-portal/rest/itajai/api/v1/pessoal"
    
    params = {
        "referencia": referencia,
        "codigo_unidade": codigo_unidade
    }
    
    try:
        # Desabilita a verificação SSL para resolver o problema de certificado
        response = requests.get(url, params=params, verify=False)
        response.raise_for_status()  # Lança exceção para erros HTTP
        return response.json()
    except Exception as e:
        print(f"Erro ao obter dados para {referencia}: {e}")
        return None

def obter_todos_registros(referencia, codigo_unidade=0):
    """
    Obtém todos os registros para uma data de referência específica.
    
    Parâmetros:
        referencia (str): Data de referência no formato "mm/aaaa"
        codigo_unidade (int): Código da unidade (0 para todas)
    
    Retorna:
        dict: Dados completos obtidos da API
    """
    print(f"Obtendo registros de {referencia} para unidade {codigo_unidade}")
    return obter_dados_pessoal(referencia, codigo_unidade)

def salvar_dados_json(dados, referencia, codigo_unidade, pasta_saida=".json"):
    """Salva os dados brutos em um arquivo JSON."""
    if not dados:
        print(f"Sem dados para salvar para {referencia}")
        return
    
    # Criar pasta de saída se não existir
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
    
    # Sanitizar referência para uso como nome de arquivo
    ref_arquivo = referencia.replace("/", "_")
    unidade_str = f"_unidade_{codigo_unidade}" if codigo_unidade > 0 else ""
    caminho_arquivo = os.path.join(pasta_saida, f"pessoal_itajai_{ref_arquivo}{unidade_str}.json")
    
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    print(f"Dados JSON salvos em {caminho_arquivo}")

def extrair_dados_intervalo(data_inicio, data_fim, codigo_unidade=0, pasta_json=".json"):
    """
    Extrai dados para um intervalo de datas e salva em arquivos JSON.
    
    Parâmetros:
        data_inicio (str): Data inicial no formato "mm/yyyy"
        data_fim (str): Data final no formato "mm/yyyy"
        codigo_unidade (int): Código da unidade (0 para todas)
        pasta_json (str): Pasta onde os arquivos JSON serão salvos
    """
    datas = criar_intervalo_datas(data_inicio, data_fim)
    
    for data in datas:
        # Converter para o formato esperado pela API (mm/aaaa)
        referencia = data
        print(f"\nProcessando dados para {referencia}, unidade {codigo_unidade}")
        
        # Obter dados para a referência
        dados = obter_todos_registros(referencia, codigo_unidade)
        
        # Salvar dados em JSON
        salvar_dados_json(dados, referencia, codigo_unidade, pasta_json)
        
        # Pausa entre solicitações de diferentes meses
        time.sleep(1)

if __name__ == "__main__":
    # Defina o intervalo de datas que deseja extrair
    data_inicio = input("Data inicial (mm/yyyy): ")
    data_fim = input("Data final (mm/yyyy): ")
    codigo_unidade = int(input("Código da unidade (0 para todas): "))
    
    # Pasta onde os arquivos serão salvos
    pasta_base = os.path.dirname(os.path.abspath(__file__))
    pasta_json = os.path.join(pasta_base, ".json2")
    
    print(f"Iniciando extração de dados de {data_inicio} até {data_fim} para unidade {codigo_unidade}")
    print(f"Os dados JSON brutos serão salvos em {pasta_json}")
    
    extrair_dados_intervalo(data_inicio, data_fim, codigo_unidade, pasta_json)
    
    print("\nExtração de dados concluída!")

