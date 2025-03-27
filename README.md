# Projeto de Dados Abertos - Itajaí

Este projeto realiza a extração, armazenamento e consulta de dados públicos do Portal da Transparência do Município de Itajaí, com foco nos dados de folha de pagamento dos servidores.

## Funcionalidades

- **Extração de Dados**: Realiza scraping dos dados do Portal da Transparência de Itajaí
- **Armazenamento em Nuvem**: Salva os dados extraídos no Azure Table Storage
- **Consulta Parametrizada**: Possibilita consultas por matrícula e período
- **Exportação para Excel**: Gera relatórios em Excel com resumo e detalhamento dos dados
- **API HTTP**: Disponibiliza os dados via Azure Function com interface HTTP

## Pré-requisitos

- Python 3.8+
- Conta Azure com Table Storage configurado
- Pacotes Python (listados em requirements.txt)

## Configuração

1. Clone o repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Configure o arquivo `.env` com as seguintes variáveis:
   ```
   AZURE_TABLE_CONNECTION_STRING=sua_connection_string
   AZURE_TABLE_NAME=nome_da_sua_tabela
   ```

## Uso

### Extração de Dados

Para extrair dados do Portal da Transparência:

```bash
python scrap_data.py
```

O script solicitará a data inicial, data final e código da unidade para extração.

### Salvamento no Azure

Para salvar os arquivos JSON extraídos no Azure Table Storage:

```bash
python save_on_azure_data_table.py
```

### Consulta de Registros

Para consultar registros de uma matrícula específica:

```bash
python load_registro.py --matricula NUMERO_MATRICULA --start_date DD/MM/AAAA --end_date DD/MM/AAAA --output resultado.xlsx
```

### API HTTP (Azure Function)

O projeto inclui uma Azure Function que pode ser implantada para fornecer acesso HTTP aos dados:

- Endpoint: `GET /api/function_app`
- Parâmetros:
  - `matricula`: Número da matrícula do servidor
  - `start_date`: Data inicial (DD/MM/AAAA)
  - `end_date`: Data final (DD/MM/AAAA)
- Retorno: Arquivo Excel com os dados da folha de pagamento

## Estrutura do Projeto

- `scrap_data.py` - Extração de dados do Portal da Transparência
- `save_on_azure_data_table.py` - Salvamento dos dados no Azure Table Storage
- `load_registro.py` - Consulta e exportação dos dados para Excel
- `function_app.py` - API HTTP via Azure Function
- `.json/` - Diretório para armazenamento dos dados extraídos

## Licença

Veja o arquivo [LICENSE](LICENSE) para detalhes.
