# Arquitetura de Dados

## Visão geral

O projeto segue a arquitetura medalhão, com camadas bronze, silver e gold. Cada camada tem um papel claro: a bronze guarda o dado bruto como veio da fonte, a silver entrega o dado limpo e tipado, e a gold (prevista para a AV2) reúne as tabelas já agregadas que respondem à pergunta de pesquisa.

**Recorte:** estado de São Paulo, de janeiro de 2020 a dezembro de 2023.
**Fonte única:** SIH/SUS, AIH Reduzida, publicada pelo DATASUS.

```text
[DATASUS, FTP publico]
         |
         v
  [Bronze]                                      <- implementado
  data/bronze/sihsus/SP/*.dbc   (48 arquivos)
  data/bronze/sihsus_sp_raw.parquet (consolidado, todos os campos)
         |
         | src/ingest_bronze.py
         v
  [Silver]                                      <- implementado
  data/silver/sihsus_sp.parquet
  Dados limpos, tipados, 17 campos selecionados
  + enriquecimento linha a linha:
    is_covid, ano, mes, ano_mes, faixa_etaria
         |
         | src/transform_silver.py
         v
  [Visualizacoes exploratorias]                 <- implementado (AV1)
  notebooks/02_silver_visualizacoes.ipynb
         |
         v
  [Gold]                                        <- previsto para a AV2
  Tabelas agregadas (series temporais, mortalidade por onda etc.)
```

## Camada Bronze (implementada)

A bronze guarda o dado cru. Nenhum schema é forçado, nenhuma coluna é descartada, nenhum tipo é convertido. A única transformação é reunir os 48 arquivos mensais em um único Parquet, o que facilita a leitura nas etapas seguintes.

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

Tem uma responsabilidade só: ler os `.dbc`, descomprimir e juntar tudo em um Parquet bruto com os 113 campos originais. Sem seleção, sem tipagem, sem filtro.

## Camada Silver (implementada)

A silver já está pronta para consumo analítico, mas continua granular: uma linha segue representando uma AIH. As agregações ficam para a gold, na AV2.

### Script responsável: `src/transform_silver.py`

As transformações são aplicadas nesta ordem:

1. **Seleção de campos.** Ficam 17 dos 113 campos originais. A tabela abaixo mostra quais.
2. **Tipagem (`clean_dtypes`).** Datas (`DT_INTER`, `DT_SAIDA`) viram `datetime`; os numéricos viram `Int64` ou `float`; as strings passam por `strip` e `upper`.
3. **Descarte de nulos.** Qualquer linha com nulo em alguma das 17 colunas é removida. Assim a silver fica garantida sem nulos.
4. **Descarte de duplicatas.** Linhas idênticas em todas as colunas são removidas.
5. **Filtro de período.** Só permanecem registros entre 2020 e 2023.
6. **Enriquecimento linha a linha.**
   - `is_covid`: booleano, `True` quando `DIAG_PRINC == 'B342'`.
   - `ano`, `mes`, `ano_mes`: derivados de `DT_INTER`.
   - `faixa_etaria`: bucketização etária nas faixas 0-4, 5-14, 15-29, 30-44, 45-59, 60-74 e 75+.
7. **Normalização Min-Max.** Para cada coluna numérica (`DIAS_PERM`, `UTI_MES_TO`, `IDADE`, `VAL_TOT`) é criada uma coluna `*_norm` no intervalo `[0, 1]`. As originais ficam preservadas.
8. **Auditoria (`audit_quality`).** No fim do pipeline rodam as asserções de invariante: sem nulos, sem duplicatas, período válido e `*_norm ∈ [0, 1]`. Se alguma falha, o pipeline para e nada é gravado.

### Campos selecionados (silver)

| Campo      | Tipo  | Descrição                                       |
| ---------- | ----- | ----------------------------------------------- |
| ANO_CMPT   | str   | Ano de processamento                            |
| MES_CMPT   | str   | Mês de processamento                            |
| DT_INTER   | date  | Data de internação                              |
| DT_SAIDA   | date  | Data de saída                                   |
| MUNIC_RES  | str   | Município de residência do paciente (cód. IBGE) |
| MUNIC_MOV  | str   | Município do estabelecimento                    |
| DIAG_PRINC | str   | Diagnóstico principal (CID-10)                  |
| MORTE      | int   | Óbito (0 = Não, 1 = Sim)                        |
| DIAS_PERM  | int   | Dias de permanência                             |
| UTI_MES_TO | int   | Dias de UTI no mês                              |
| CAR_INT    | str   | Caráter da internação (eletiva/urgência)        |
| COMPLEX    | str   | Nível de complexidade                           |
| SEXO       | str   | Sexo do paciente                                |
| IDADE      | int   | Idade do paciente                               |
| COD_IDADE  | str   | Unidade de medida da idade (4 = anos)           |
| VAL_TOT    | float | Valor total da AIH (R$)                         |
| CNES       | str   | Código CNES do estabelecimento                  |

### Colunas derivadas adicionadas na silver

| Coluna            | Origem                | Descrição                            |
| ----------------- | --------------------- | ------------------------------------ |
| `is_covid`        | `DIAG_PRINC`          | `True` quando CID == `B342`          |
| `ano`             | `DT_INTER`            | Ano da internação                    |
| `mes`             | `DT_INTER`            | Mês da internação (1 a 12)           |
| `ano_mes`         | `DT_INTER`            | Primeiro dia do mês (série temporal) |
| `faixa_etaria`    | `IDADE` + `COD_IDADE` | Bucketização etária (anos completos) |
| `DIAS_PERM_norm`  | `DIAS_PERM`           | Min-Max normalizado em `[0, 1]`      |
| `UTI_MES_TO_norm` | `UTI_MES_TO`          | Min-Max normalizado em `[0, 1]`      |
| `IDADE_norm`      | `IDADE`               | Min-Max normalizado em `[0, 1]`      |
| `VAL_TOT_norm`    | `VAL_TOT`             | Min-Max normalizado em `[0, 1]`      |

> **Nota sobre agregações:** a silver **não** contém tabelas agregadas. Todas as colunas derivadas são calculadas linha a linha. Séries mensais, mortalidade por onda e afins são escopo da gold, na AV2.

## Visualizações (AV1)

As visualizações exploratórias das variáveis da silver estão em `notebooks/02_silver_visualizacoes.ipynb`. Elas são calculadas em memória sobre a silver granular. Nada é persistido em disco.

## Camada Gold (prevista para a AV2)

Escopo da AV2: tabelas agregadas prontas para responder à pergunta de pesquisa, como volume mensal por CID, taxa de mortalidade por onda e perfil de uso da UTI.

## Tecnologias

| Camada        | Tecnologia                       | Por que foi escolhida                                          |
| ------------- | -------------------------------- | -------------------------------------------------------------- |
| Ingestão      | `datasus-dbc`, `dbfread`         | São as bibliotecas que leem `.dbc` sem precisar converter fora |
| Processamento | `pandas`                         | Atende com folga o volume atual e o time já domina             |
| Armazenamento | Parquet via `pyarrow`            | Formato colunar e comprimido, bom para consultas analíticas    |
| Análise       | Jupyter, `matplotlib`, `seaborn` | Ferramentas usuais para exploração e gráficos estáticos        |

### Tecnologias pagas que poderiam entrar em uma versão profissional

| Tecnologia   | Papel no pipeline                                 | Motivo de não usar agora                   |
| ------------ | ------------------------------------------------- | ------------------------------------------ |
| AWS S3       | Armazenar bronze, silver e gold de forma durável  | Custo, o projeto roda na máquina do aluno  |
| Apache Spark | Processar a silver de forma distribuída           | O volume atual (48 arquivos) não justifica |
| dbt          | Transformações gold versionadas e testadas        | Complexidade fora do escopo da AV1         |
| Airflow      | Orquestrar o pipeline ponta a ponta               | Idem                                       |
| Databricks   | Lakehouse unificado para bronze, silver e gold    | Idem                                       |

## Qualidade dos dados

| Problema       | Descrição                                                     | Tratamento                                                       |
| -------------- | ------------------------------------------------------------- | ---------------------------------------------------------------- |
| Campos legados | 19 campos zerados desde 2015                                  | Descartados já na seleção da silver                              |
| Nulos          | Qualquer coluna nula entre as 17 selecionadas                 | Linha descartada, garantido por `drop_nulls` e `audit_quality`   |
| Duplicatas     | Linhas idênticas em todas as colunas                          | Removidas por `drop_duplicates`                                  |
| Encoding       | Arquivos em latin-1                                           | Encoding declarado explicitamente na leitura                     |
| CID do COVID   | O DATASUS usa `B342`, e não `U071` ou `U072`                  | A flag `is_covid` usa `B342`                                     |
| Escalas        | Variáveis numéricas em unidades diferentes                    | Colunas `*_norm` Min-Max em `[0, 1]`                             |
| Invariantes    | Nulos, duplicatas, período e intervalos de normalização       | `audit_quality` roda as asserções no fim do pipeline             |
