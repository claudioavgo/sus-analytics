# SUS Analytics: impacto do COVID-19 nas internações hospitalares (SP, 2020-2023)

## Pergunta de pesquisa

Como as ondas do COVID-19 impactaram o volume de internações e a mortalidade hospitalar no SUS-SP entre 2020 e 2023?

Perguntas secundárias:

- Como evoluiu, mês a mês, o volume de internações por COVID (CID B342) em São Paulo?
- A taxa de óbito hospitalar subiu durante os picos da pandemia?
- O perfil da internação (dias de permanência e uso de UTI) mudou de uma onda para outra?
- Quais grupos demográficos (sexo e faixa etária) foram mais afetados?

## Contexto

São Paulo concentra a maior rede hospitalar do SUS e registrou os maiores picos de internação por COVID no país. Por isso, a base SIH/SUS restrita ao estado oferece volume suficiente e recorte geográfico coeso para o estudo proposto, sem inflar o pipeline com dados que não responderiam à pergunta de pesquisa.

## Fonte de dados

| Fonte             | Descrição                                          | Formato | Cobertura               |
| ----------------- | -------------------------------------------------- | ------- | ----------------------- |
| SIH/SUS (DATASUS) | Autorizações de Internação Hospitalar, AIH Reduzida | `.dbc`  | SP, Jan/2020 a Dez/2023 |

Os dados brutos ficam em `data/bronze/`, dentro da arquitetura medalhão (bronze, silver e gold).

## Estrutura do projeto

```text
data/
  bronze/
    sihsus/
      SP/                      # 48 arquivos .dbc, Jan/2020 a Dez/2023
      docs/                    # Layout oficial DATASUS (IT_SIHSUS)
    sihsus_sp_raw.parquet      # Parquet bruto consolidado, gerado pelo pipeline
  silver/
    sihsus_sp.parquet          # Dados limpos, tipados e enriquecidos
src/
  ingest_bronze.py             # .dbc -> Parquet bruto (bronze)
  transform_silver.py          # bronze -> silver, limpa, tipada e enriquecida
notebooks/
  01_exploracao_sihsus.ipynb   # Demonstração técnica da ingestão e da transformação
  02_silver_visualizacoes.ipynb # Visualizações exploratórias das variáveis da silver
docs/
  arquitetura_dados.md         # Arquitetura do pipeline de dados
  arquitetura_dados.docx       # Mesma arquitetura em DOCX, entrega oficial da AV1
  checklist_av1.md             # Checklist de status das etapas da AV1
  team_roles.md                # Divisão de tarefas da equipe
  PROJETO_FUND_BIG_DATA.pdf    # Especificação da disciplina
requirements.txt
```

## Pipeline de dados

```text
[DATASUS]
    |
    v
[Bronze] data/bronze/sihsus/SP/*.dbc
    | src/ingest_bronze.py
    | - descomprime .dbc -> DataFrame
    | - consolida os 48 arquivos em um unico Parquet bruto (113 campos)
    v
[Bronze consolidado] data/bronze/sihsus_sp_raw.parquet
    | src/transform_silver.py
    | - seleciona 17 campos relevantes
    | - tipagem (datas, numericos, categoricos)
    | - filtra 2020-2023 e datas invalidas
    | - enriquece linha a linha: is_covid, ano, mes, ano_mes, faixa_etaria
    v
[Silver] data/silver/sihsus_sp.parquet
    |
    v
[Notebooks] 01_exploracao_sihsus.ipynb  (demonstracao tecnica)
            02_silver_visualizacoes.ipynb (visualizacoes das variaveis, AV1)
```

> A camada gold, com as tabelas agregadas já consolidadas, é escopo da AV2.

## Tecnologias utilizadas

| Camada        | Tecnologia                                |
| ------------- | ----------------------------------------- |
| Leitura .dbc  | `datasus-dbc`, `dbfread`                  |
| Processamento | `pandas`, `pyarrow`                       |
| Armazenamento | Parquet (via `pyarrow`)                   |
| Visualização  | Jupyter Notebook, `matplotlib`, `seaborn` |
| Versionamento | Git e GitHub                              |

## Como executar

```bash
# 1. Instalar as dependências
pip install -r requirements.txt

# 2. Rodar a ingestão bruta (bronze)
python src/ingest_bronze.py

# 3. Rodar a transformação (bronze -> silver)
python src/transform_silver.py

# 4. Abrir os notebooks
jupyter notebook notebooks/01_exploracao_sihsus.ipynb
jupyter notebook notebooks/02_silver_visualizacoes.ipynb
```

## Licença

Dados públicos do DATASUS, Ministério da Saúde.
