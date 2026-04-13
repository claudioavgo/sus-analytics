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
  silver/          # Dados limpos e tipados (gerado pelo pipeline)
src/
  ingest.py        # Leitura de .dbc para DataFrame (bronze -> silver)
  transform.py     # Funções de transformação demonstradas no notebook
notebooks/
  01_exploracao_sihsus.ipynb   # Demonstração técnica da ingestão e transformação
docs/
  arquitetura_dados.md         # Arquitetura do pipeline de dados
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
    | src/ingest.py
    | - descomprime .dbc -> .dbf
    | - seleciona 17 campos relevantes
    | - exporta Parquet consolidado
    v
[Silver] data/silver/sihsus_sp.parquet
    | src/transform.py (funções demonstradas no notebook)
    | - tipagem correta (datas, numéricos, categóricos)
    | - filtragem: período 2020-2023
    | - flag COVID: DIAG_PRINC == B342 (CID usado pelo DATASUS)
    | - colunas derivadas: ano, mês, ano_mes, faixa_etaria
    v
[Notebook] notebooks/01_exploracao_sihsus.ipynb
```

## Tecnologias utilizadas

| Camada               | Tecnologia                     |
| -------------------- | ------------------------------ |
| Leitura .dbc         | `datasus-dbc`, `dbfread`       |
| Processamento        | `pandas`, `pyarrow`            |
| Armazenamento        | Parquet (via `pyarrow`)        |
| Demonstração técnica | Jupyter Notebook, `matplotlib` |
| Versionamento        | Git / GitHub                   |

## Como executar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar ingestão (bronze -> silver)
python src/ingest.py

# 3. Abrir notebook de demonstração técnica
jupyter notebook notebooks/01_exploracao_sihsus.ipynb
```

## Licença

Dados públicos disponibilizados pelo DATASUS/Ministério da Saúde.
