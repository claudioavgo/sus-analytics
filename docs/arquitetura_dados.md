# Arquitetura de Dados

## Visão geral

O projeto segue a arquitetura medalhão (bronze/silver/gold) para organizar o fluxo de dados
desde a ingestão bruta até as tabelas analíticas prontas para responder a pergunta de pesquisa.

**Recorte:** Estado de Sao Paulo (SP), Janeiro/2020 a Dezembro/2023.
**Fonte única:** SIH/SUS — AIH Reduzida (DATASUS).

```text
[DATASUS — FTP publico]
         |
         v
  [Bronze Layer]                    <- implementado
  data/bronze/sihsus/SP/
  48 arquivos .dbc (1 por mes, 4 anos)
         |
         | src/ingest.py
         v
  [Silver Layer]                    <- implementado
  data/silver/sihsus_sp.parquet
  Dados limpos, tipados, campos relevantes selecionados
         |
         | src/transform.py         <- funcoes implementadas, demonstradas no notebook
         v
  [Gold Layer]                      <- planejado para AV2
  data/gold/
  Tabela analitica com flag COVID, series temporais, metricas de gravidade
         |
         v
  [Analise e Visualizacoes]         <- planejado para AV2
  notebooks/
```

## Camada Bronze (implementada)

Dados brutos sem nenhuma transformação, exatamente como obtidos do DATASUS.

```text
data/bronze/
  sihsus/
    SP/
      RDSP2001.dbc  ...  RDSP2312.dbc   # 48 arquivos (Jan/2020 a Dez/2023)
    docs/
      IT_SIHSUS_1603.pdf                # Layout oficial DATASUS
```

### Volume

| Fonte   | Arquivos | Formato               |
| ------- | -------- | --------------------- |
| SIH/SUS | 48       | .dbc (DBF comprimido) |

## Camada Silver (implementada via src/ingest.py)

Dados descomprimidos, limpos e com campos selecionados para a pesquisa.

### Transformações aplicadas

- Descompressão `.dbc` -> leitura via `datasus_dbc` + `dbfread`
- Selecão dos campos relevantes (ver tabela abaixo)
- Tipagem correta: datas (`DT_INTER`, `DT_SAIDA`) como `datetime`, numéricos como `int`/`float`
- Remoção de campos legados zerados (19 campos sem conteúdo desde 2015)
- Exportação em formato Parquet consolidado

### Campos selecionados (silver)

| Campo      | Tipo  | Descricao                                       |
| ---------- | ----- | ----------------------------------------------- |
| ANO_CMPT   | str   | Ano de processamento                            |
| MES_CMPT   | str   | Mês de processamento                            |
| DT_INTER   | date  | Data de internação                              |
| DT_SAIDA   | date  | Data de saída                                   |
| MUNIC_RES  | str   | Município de residência do paciente (cod. IBGE) |
| MUNIC_MOV  | str   | Município do estabelecimento                    |
| DIAG_PRINC | str   | Diagnóstico principal (CID-10)                  |
| MORTE      | int   | Óbito (0=Não, 1=Sim)                            |
| DIAS_PERM  | int   | Dias de permanência                             |
| UTI_MES_TO | int   | Dias de UTI no mês                              |
| CAR_INT    | str   | Caráter da internação (eletiva/urgência)        |
| COMPLEX    | str   | Nível de complexidade                           |
| SEXO       | str   | Sexo do paciente                                |
| IDADE      | int   | Idade do paciente                               |
| COD_IDADE  | str   | Unidade de medida da idade (4=Anos)             |
| VAL_TOT    | float | Valor total da AIH (R$)                         |
| CNES       | str   | Código CNES do estabelecimento                  |

## Funcoes de transformacao (src/transform.py)

As funções abaixo estão implementadas e são demonstradas no notebook de AV1.
A execução completa do pipeline (geração da camada gold) é escopo da AV2.

| Função            | Descrição                                                  |
| ----------------- | ---------------------------------------------------------- |
| `add_covid_flag`  | Adiciona coluna `is_covid` (DIAG_PRINC == 'B342')          |
| `add_time_columns`| Adiciona `ano`, `mes`, `ano_mes` a partir de `DT_INTER`    |
| `add_age_group`   | Adiciona `faixa_etaria` (0-4, 5-14, ..., 75+)              |
| `filter_period`   | Filtra registros para o período 2020-2023                  |

## Tecnologias

| Camada   | Tecnologia                       | Justificativa                                           |
| -------- | -------------------------------- | ------------------------------------------------------- |
| Ingestão | `datasus-dbc`, `dbfread`         | Unicas libs que leem .dbc nativo sem conversao externa  |
| Processo | `pandas`                         | Padrão de mercado para ETL em escala de milhões de rows |
| Storage  | Parquet (`pyarrow`)              | Colunar, comprimido, ideal para queries analíticas      |
| Análise  | Jupyter, `matplotlib`, `seaborn` | Padrão acadêmico e de mercado para EDA e storytelling   |

### Tecnologias pagas que poderiam ser usadas em cenário profissional

| Tecnologia   | Papel no pipeline                           | Motivo da não adocao               |
| ------------ | ------------------------------------------- | ---------------------------------- |
| AWS S3       | Storage das camadas bronze/silver/gold      | Custo — projeto acadêmico local    |
| Apache Spark | Processamento distribuído da silver         | Escala não justifica (48 arquivos) |
| dbt          | Transformações gold documentadas e testadas | Complexidade acima do escopo AV1   |
| Airflow      | Orquestração do pipeline completo           | Idem                               |
| Databricks   | Plataforma unificada lakehouse              | Idem                               |

## Qualidade dos dados

| Problema        | Descrição                                             | Tratamento          |
| --------------- | ----------------------------------------------------- | ------------------- |
| Campos zerados  | 19 campos legados sem conteúdo (ex: VAL_SADT, VAL_RN) | Removidos na silver |
| Datas inválidas | Registros com DT_INTER ou DT_SAIDA fora do período    | Filtrados na silver |
| Encoding        | Arquivos em latin-1                                   | Declarado na leitura|
| CID COVID       | DATASUS registra como B342, nao U071/U072             | Flag usa B342       |
