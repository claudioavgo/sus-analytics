# SUS Analytics — Impacto do COVID-19 nas Internações Hospitalares (SP, 2020-2023)

## Pergunta de pesquisa

Como as ondas do COVID-19 impactaram o volume de internações e a mortalidade hospitalar no SUS-SP entre 2020 e 2023?

Sub-perguntas:

- Como evoluiu mês a mês o volume de internações por COVID (CID B342) em SP?
- A taxa de óbitos hospitalares aumentou durante os picos de COVID?
- Houve diferença no perfil da internação (dias de permanência, uso de UTI) entre as ondas?
- Quais grupos demográficos (sexo, faixa etária) foram mais impactados?

## Contexto

O COVID-19 gerou uma das maiores pressões sobre o sistema hospitalar brasileiro da história recente.
São Paulo, como o estado mais populoso e com maior rede hospitalar do SUS, representa um
laboratório ideal para entender como o sistema respondeu às ondas da pandemia entre 2020 e 2023.

## Fonte de dados

| Fonte             | Descrição                                            | Formato | Cobertura               |
| ----------------- | ---------------------------------------------------- | ------- | ----------------------- |
| SIH/SUS (DATASUS) | Autorizações de Internação Hospitalar - AIH Reduzida | `.dbc`  | SP, Jan/2020 a Dez/2023 |

Os dados brutos estão organizados em `data/bronze/`, seguindo arquitetura medalhão (bronze/silver/gold).

## Estrutura do projeto

```text
data/
  bronze/
    sihsus/
      SP/          # 48 arquivos .dbc — Jan/2020 a Dez/2023
      docs/        # Layout oficial DATASUS (IT_SIHSUS)
    sihsus_sp_raw.parquet   # Parquet bruto consolidado (gerado pelo pipeline)
  silver/
    sihsus_sp.parquet       # Dados limpos, tipados e enriquecidos (gerado pelo pipeline)
src/
  ingest_bronze.py          # .dbc -> Parquet bruto (camada bronze)
  transform_silver.py       # Bronze raw -> Silver limpa, tipada e enriquecida
notebooks/
  01_exploracao_sihsus.ipynb      # Demonstração técnica da ingestão e transformação
  02_silver_visualizacoes.ipynb   # Visualizações exploratórias das variáveis da silver
docs/
  arquitetura_dados.md      # Arquitetura do pipeline de dados
  checklist_av1.md          # Checklist de status das etapas da AV1
  team_roles.md             # Divisão de tarefas da equipe
  PROJETO_FUND_BIG_DATA.pdf # Especificação da disciplina
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
    | - consolida 48 arquivos em 1 Parquet bruto (113 campos)
    v
[Bronze consolidado] data/bronze/sihsus_sp_raw.parquet
    | src/transform_silver.py
    | - seleciona 17 campos relevantes
    | - tipagem (datas, numéricos, categóricos)
    | - filtra período 2020-2023 e datas inválidas
    | - enriquece linha-a-linha: is_covid, ano, mes, ano_mes, faixa_etaria
    v
[Silver] data/silver/sihsus_sp.parquet
    |
    v
[Notebooks] 01_exploracao_sihsus.ipynb  (demonstração técnica)
            02_silver_visualizacoes.ipynb (visualizações das variáveis)
```

> A camada Gold (agregações e tabelas analíticas consolidadas) é escopo da AV2.

## Tecnologias utilizadas

| Camada               | Tecnologia                                |
| -------------------- | ----------------------------------------- |
| Leitura .dbc         | `datasus-dbc`, `dbfread`                  |
| Processamento        | `pandas`, `pyarrow`                       |
| Armazenamento        | Parquet (via `pyarrow`)                   |
| Visualização         | Jupyter Notebook, `matplotlib`, `seaborn` |
| Versionamento        | Git / GitHub                              |

## Como executar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar ingestão bruta (bronze)
python src/ingest_bronze.py

# 3. Executar transformação (bronze -> silver)
python src/transform_silver.py

# 4. Abrir notebooks
jupyter notebook notebooks/01_exploracao_sihsus.ipynb
jupyter notebook notebooks/02_silver_visualizacoes.ipynb
```

## Licença

Dados públicos disponibilizados pelo DATASUS/Ministério da Saúde.
