# Arquitetura de Dados

## Visão geral

O projeto segue a arquitetura medalhão (bronze/silver/gold) para organizar o fluxo de dados
desde a ingestão bruta até as tabelas analíticas prontas para responder à pergunta de pesquisa.

**Recorte:** Estado de São Paulo (SP), Janeiro/2020 a Dezembro/2023.
**Fonte única:** SIH/SUS — AIH Reduzida (DATASUS).

```text
[DATASUS — FTP publico]
         |
         v
  [Bronze Layer]                                <- implementado
  data/bronze/sihsus/SP/*.dbc   (48 arquivos)
  data/bronze/sihsus_sp_raw.parquet (consolidado, todos os campos)
         |
         | src/ingest_bronze.py
         v
  [Silver Layer]                                <- implementado
  data/silver/sihsus_sp.parquet
  Dados limpos, tipados, 17 campos selecionados
  + enriquecimento linha-a-linha:
    is_covid, ano, mes, ano_mes, faixa_etaria
         |
         | src/transform_silver.py
         v
  [Visualizacoes exploratorias]                 <- implementado (AV1)
  notebooks/02_silver_visualizacoes.ipynb
         |
         v
  [Gold Layer]                                  <- planejado para AV2
  Tabelas agregadas (series temporais, mortalidade por onda, etc.)
```

## Camada Bronze (implementada)

Dados brutos e Parquet consolidado, sem nenhuma transformação de schema ou tipo.

```text
data/bronze/
  sihsus/
    SP/
      RDSP2001.dbc  ...  RDSP2312.dbc   # 48 arquivos (Jan/2020 a Dez/2023)
    docs/
      IT_SIHSUS_1603.pdf                # Layout oficial DATASUS
  sihsus_sp_raw.parquet                 # Consolidado pelo src/ingest_bronze.py
```

### Volume

| Fonte   | Arquivos | Formato               |
| ------- | -------- | --------------------- |
| SIH/SUS | 48       | .dbc (DBF comprimido) |

### Script responsável: `src/ingest_bronze.py`

Responsabilidade única: **ler os `.dbc`, descomprimir e consolidar** em um Parquet
bruto com todos os 113 campos originais, sem seleção ou tipagem.

## Camada Silver (implementada)

Dados limpos, tipados, com campos selecionados e enriquecidos linha-a-linha
(sem agregação). Uma linha = uma AIH.

### Script responsável: `src/transform_silver.py`

Transformações aplicadas em ordem:

1. **Seleção de campos** — 17 dos 113 campos originais (ver tabela abaixo)
2. **Tipagem (`clean_dtypes`)** — datas (`DT_INTER`, `DT_SAIDA`) como `datetime`; numéricos como `Int64`/`float`; strings normalizadas (`strip` + `upper`)
3. **Drop de nulos** — linhas com qualquer valor nulo em qualquer uma das 17 colunas são descartadas. A silver é garantida **sem nulos**.
4. **Drop de duplicatas** — linhas idênticas em todas as colunas são removidas.
5. **Filtro de período** — apenas 2020-2023
6. **Enriquecimento** (colunas derivadas linha-a-linha):
   - `is_covid` — booleano, `DIAG_PRINC == 'B342'`
   - `ano`, `mes`, `ano_mes` — derivados de `DT_INTER`
   - `faixa_etaria` — bucketizacao etaria (0-4, 5-14, 15-29, 30-44, 45-59, 60-74, 75+)
7. **Normalização Min-Max** — para cada coluna numérica (`DIAS_PERM`, `UTI_MES_TO`, `IDADE`, `VAL_TOT`) é criada uma coluna `*_norm` no intervalo `[0, 1]`. As colunas originais são preservadas.
8. **Auditoria de qualidade (`audit_quality`)** — asserções invariantes (sem nulos, sem duplicatas, período válido, `*_norm ∈ [0,1]`) + relatório de estatísticas logadas. Interrompe o pipeline se alguma invariante falhar.

### Campos selecionados (silver)

| Campo      | Tipo  | Descrição                                       |
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

### Colunas derivadas adicionadas na silver

| Coluna            | Origem                         | Descrição                                |
| ----------------- | ------------------------------ | ---------------------------------------- |
| `is_covid`        | `DIAG_PRINC`                   | `True` quando CID == `B342`              |
| `ano`             | `DT_INTER`                     | Ano da internação                        |
| `mes`             | `DT_INTER`                     | Mês da internação (1-12)                 |
| `ano_mes`         | `DT_INTER`                     | Primeiro dia do mês (série temporal)     |
| `faixa_etaria`    | `IDADE` + `COD_IDADE`          | Bucketização etária (anos completos)     |
| `DIAS_PERM_norm`  | `DIAS_PERM`                    | Min-Max normalizado em `[0, 1]`          |
| `UTI_MES_TO_norm` | `UTI_MES_TO`                   | Min-Max normalizado em `[0, 1]`          |
| `IDADE_norm`      | `IDADE`                        | Min-Max normalizado em `[0, 1]`          |
| `VAL_TOT_norm`    | `VAL_TOT`                      | Min-Max normalizado em `[0, 1]`          |

> **Nota sobre agregações:** a camada silver **não** contém tabelas agregadas.
> Todas as colunas derivadas são calculadas linha-a-linha. Agregações (séries
> mensais, mortalidade por onda, etc.) são escopo da camada Gold, na AV2.

## Visualizações (AV1)

As visualizações exploratórias das variáveis da silver estão em
`notebooks/02_silver_visualizacoes.ipynb`. Elas são calculadas em memória
sobre a silver granular — nada é persistido em disco.

## Camada Gold (planejada — AV2)

Escopo da AV2: tabelas agregadas prontas para responder à pergunta de pesquisa
(volume mensal por CID, taxa de mortalidade por onda, perfil UTI, etc.).

## Tecnologias

| Camada   | Tecnologia                       | Justificativa                                           |
| -------- | -------------------------------- | ------------------------------------------------------- |
| Ingestão | `datasus-dbc`, `dbfread`         | Unicas libs que leem .dbc nativo sem conversao externa  |
| Processo | `pandas`                         | Padrão de mercado para ETL em escala de milhões de rows |
| Storage  | Parquet (`pyarrow`)              | Colunar, comprimido, ideal para queries analíticas      |
| Análise  | Jupyter, `matplotlib`, `seaborn` | Padrão acadêmico e de mercado para EDA e storytelling   |

### Tecnologias pagas que poderiam ser usadas em cenário profissional

| Tecnologia   | Papel no pipeline                           | Motivo da não adoção               |
| ------------ | ------------------------------------------- | ---------------------------------- |
| AWS S3       | Storage das camadas bronze/silver/gold      | Custo — projeto acadêmico local    |
| Apache Spark | Processamento distribuído da silver         | Escala não justifica (48 arquivos) |
| dbt          | Transformações gold documentadas e testadas | Complexidade acima do escopo AV1   |
| Airflow      | Orquestração do pipeline completo           | Idem                               |
| Databricks   | Plataforma unificada lakehouse              | Idem                               |

## Qualidade dos dados

| Problema        | Descrição                                             | Tratamento           |
| --------------- | ----------------------------------------------------- | -------------------- |
| Campos legados  | 19 campos zerados desde 2015                          | Descartados na silver|
| Nulos           | Qualquer coluna nula nos 17 campos selecionados       | Linha descartada (garantia via `drop_nulls` + `audit_quality`) |
| Duplicatas      | Linhas idênticas em todas as colunas                  | Removidas via `drop_duplicates` |
| Encoding        | Arquivos em latin-1                                   | Declarado na leitura |
| CID COVID       | DATASUS registra como B342, não U071/U072             | Flag usa B342        |
| Escalas         | Variáveis numéricas em unidades diferentes            | Colunas `*_norm` Min-Max em `[0,1]` |
| Invariantes     | Nulos / duplicatas / período / ranges de normalizacao | `audit_quality` executa asserções no fim do pipeline |
