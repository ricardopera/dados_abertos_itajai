import azure.data.tables as adt
import json
import os

from datetime import datetime, timedelta

from dotenv import load_dotenv

from time import sleep

load_dotenv()
# Carregar variáveis de ambiente do arquivo .env
AZURE_TABLE_CONNECTION_STRING = os.getenv("AZURE_TABLE_CONNECTION_STRING")
AZURE_TABLE_NAME = os.getenv("AZURE_TABLE_NAME")

# Verifica se as variáveis de ambiente estão definidas
if not AZURE_TABLE_CONNECTION_STRING or not AZURE_TABLE_NAME:
    raise ValueError("As variáveis de ambiente AZURE_TABLE_CONNECTION_STRING e AZURE_TABLE_NAME devem estar definidas.")

# Conexão com o Azure Table Storage
table_service = adt.TableServiceClient.from_connection_string(AZURE_TABLE_CONNECTION_STRING)
table_client = table_service.get_table_client(AZURE_TABLE_NAME)

# Função para salvar dados no Azure Table Storage
def salvar_dados_azure(dados, referencia, codigo_unidade):
    """
    Salva os dados no Azure Table Storage.
    
    Parâmetros:
        dados (dict): Dados a serem salvos
        referencia (str): Data de referência no formato "mm/aaaa"
        codigo_unidade (int): Código da unidade (0 para todas)
    """
    try:
        # Verifica se os dados têm a estrutura esperada
        if "registros" not in dados:
            print(f"Estrutura de dados inválida para referência {referencia}")
            return
            
        # Cria uma entidade para cada registro (em ordem inversa)
        registros_encontrados = 0
        registros_existentes = 0
        registros_total = len(dados["registros"])
        
        # Inverte a ordem dos registros para processamento
        for item in reversed(dados["registros"]):
            if "registro" not in item:
                continue
                
            registro = item["registro"]
            registros_encontrados += 1
            
            # Verifica se matrícula existe no registro
            if "matricula" not in registro or "numero" not in registro["matricula"]:
                print(f"Registro sem matrícula válida ignorado")
                continue
                
            # Cria a entidade com os campos principais
            entity = {
                "PartitionKey": registro["matricula"]["numero"],
                "RowKey": referencia.replace("/", "_"),
                "referencia": referencia,
                "codigo_unidade": codigo_unidade,
            }
            
            # Adiciona informações básicas
            if "informacao" in dados:
                entity["informacao"] = dados["informacao"]
            if "ultimaAtualizacao" in dados:
                entity["ultimaAtualizacao"] = dados["ultimaAtualizacao"]
                
            # Adiciona dados do registro de forma serializada para evitar problemas de estrutura
            entity["dados_json"] = json.dumps(registro)
            
            # Tenta criar a entidade com tratamento específico para entidades existentes
            max_tentativas = 7
            tentativa = 0
            while tentativa < max_tentativas:
                try:
                    table_client.create_entity(entity=entity)
                    break  # Sucesso, sai do loop
                except Exception as e:
                    erro_str = str(e)
                    # Verifica se o erro é de entidade que já existe
                    if "EntityAlreadyExists" in erro_str:
                        registros_existentes += 1
                        print(f"Registro {registros_encontrados}/{registros_total} já existe. Entidade: {entity['PartitionKey']} - {entity['RowKey']}")
                        break  # Sai do loop, o registro já existe
                    else:
                        # Para outros erros, tenta novamente
                        tentativa += 1
                        print(f"Erro ao salvar registro (tentativa {tentativa}/{max_tentativas}): {e}")
                        if tentativa == max_tentativas:
                            print(f"Falha ao salvar registro após {max_tentativas} tentativas.")
                        else:
                            sleep(1)  # Aguarda um pouco antes de tentar novamente
            
            # Se todos os registros já existem, podemos parar o processamento
            if registros_existentes >= 5 and registros_encontrados >= 10:
                print(f"Múltiplos registros já existem para {referencia} na unidade {codigo_unidade}. Pulando para o próximo arquivo.")
                return
            
        print(f"Dados salvos com sucesso para {referencia} na unidade {codigo_unidade}. Processados: {registros_encontrados}, já existentes: {registros_existentes}")
    except Exception as e:
        print(f"Erro ao salvar dados no Azure: {e}")


# Função para ler arquivo JSON da pasta .json e salvar no Azure Table Storage (exemplo de nome de arquivo: pessoal_itajai_01_2019_unidade_1.json)
def ler_e_salvar_azure(arquivo_json, codigo_unidade):
    """
    Lê um arquivo JSON e salva os dados no Azure Table Storage.
    
    Parâmetros:
        arquivo_json (str): Caminho do arquivo JSON
        codigo_unidade (int): Código da unidade (0 para todas)
    """
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as file:
            dados = json.load(file)
            ref_split = os.path.basename(arquivo_json).split('_')
            referencia = ref_split[2] + '/' + ref_split[3]
            salvar_dados_azure(dados, referencia, codigo_unidade)
    except Exception as e:
        print(f"Erro ao ler o arquivo {arquivo_json}: {e}")

if __name__ == "__main__":
    # Lê todos os arquivos da pasta .json e salva no Azure Table Storage
    pasta_json = ".json"
    arquivos_json = [f for f in os.listdir(pasta_json) if f.endswith('.json')]

    for arquivo in arquivos_json:
        arquivo_json = os.path.join(pasta_json, arquivo)
        # Extrai o código da unidade do nome do arquivo (exemplo: unidade_1)
        codigo_unidade = int(arquivo.split('_unidade_')[1].split('.')[0]) if '_unidade_' in arquivo else 0
        ler_e_salvar_azure(arquivo_json, codigo_unidade)
        print(f"Arquivo {arquivo_json} processado e salvo no Azure Table Storage.")
        # Adicione um pequeno atraso para evitar sobrecarga na API do Azure
        sleep(0.5)
