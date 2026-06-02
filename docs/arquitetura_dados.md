# Arquitetura de Dados

## Visão geral

O projeto segue a arquitetura medalhão, com camadas bronze, silver e gold. Cada camada tem um papel claro: a bronze guarda o dado bruto como veio da fonte, a silver entrega o dado limpo e tipado, e a gold reúne as tabelas já agregadas que respondem à pergunta de pesquisa. O destino final do pipeline são as visualizações: um dashboard interativo e os notebooks de análise.

**Recorte:** estado de São Paulo, de janeiro de 2020 a dezembro de 2023.
**Fonte única:** SIH/SUS, AIH Reduzida, publicada pelo DATASUS.

```text
[DATASUS, FTP público]
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
  [Visualizações exploratórias]                 <- implementado (AV1)
  notebooks/02_silver_visualizacoes.ipynb
         |
         | src/build_gold.py
         v
  [Gold]                                        <- implementado (AV2)
  data/gold/*.parquet e *.csv
  5 tabelas agregadas: serie_mensal, ondas,
  perfil_covid_vs_outros, demografia_covid, municipios_covid
         |
         | src/build_dashboard.py / notebooks/03_gold_analise.ipynb
         v
  [Destino: consumo]                            <- implementado (AV2)
  output/dashboard.html (interativo) + output/figuras/*.png
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

> **Nota sobre agregações:** a silver **não** contém tabelas agregadas. Todas as colunas derivadas são calculadas linha a linha. Séries mensais, mortalidade por onda e afins ficam na gold (ver seção da camada gold).

## Visualizações exploratórias (AV1)

As visualizações exploratórias das variáveis da silver estão em `notebooks/02_silver_visualizacoes.ipynb`. Elas são calculadas em memória sobre a silver granular. Nada é persistido em disco. As visualizações de resultado, consolidadas, estão na camada de destino descrita acima (dashboard e notebook 03).

## Camada Gold (implementada)

A gold reúne as tabelas agregadas prontas para responder à pergunta de pesquisa. É gerada pelo `src/build_gold.py` a partir da silver e salva em `data/gold/`, em Parquet (consumo analítico) e CSV (inspeção e versionamento). Por serem pequenas, as tabelas gold ficam versionadas no repositório.

### Script responsável: `src/build_gold.py`

Primeiro rotula cada internação com a onda da pandemia (`add_onda`) e então materializa cinco tabelas:

| Tabela | Conteúdo | Responde |
| ------ | -------- | -------- |
| `serie_mensal` | Internações e óbitos por mês (COVID vs outros) e taxas | Evolução mensal e mortalidade |
| `ondas` | Volume, letalidade, UTI, permanência e idade por onda | Perfil por onda |
| `perfil_covid_vs_outros` | Comparativo clínico COVID frente aos demais motivos | Gravidade da COVID |
| `demografia_covid` | Internações, óbitos e letalidade por sexo e faixa etária | Grupos mais afetados |
| `municipios_covid` | Top 20 municípios por internação COVID | Concentração geográfica |

### Definição das ondas

As janelas das ondas foram definidas a partir dos picos observados na própria série mensal de internações por COVID (CID B342), e não por datas arbitrárias:

| Onda | Janela | Pico |
| ---- | ------ | ---- |
| Onda 1 (vírus original) | Jan/2020 a Out/2020 | Jul/2020 |
| Onda 2 (variante Gama) | Nov/2020 a Out/2021 | Mar/2021 (45.180) |
| Onda 3 (variante Ômicron) | Nov/2021 a Abr/2022 | Jan/2022 |
| Período endêmico | Mai/2022 a Dez/2023 | sem pico relevante |

## Camada de destino: visualizações (implementada)

O destino final do pipeline são as visualizações de resultado.

- **`src/build_dashboard.py`** lê a gold e monta `output/dashboard.html`, um dashboard único, interativo e auto-contido (Plotly embutido, funciona offline). O mesmo script exporta as figuras estáticas em `output/figuras/*.png`, usadas no README. As funções de figura ficam nesse módulo e são reaproveitadas pelo notebook, garantindo uma única fonte de verdade visual.
- **`notebooks/03_gold_analise.ipynb`** consome a gold, responde às sub-perguntas com leitura crítica e dispara a geração do dashboard.
- **`notebooks/00_pipeline_evidencias.ipynb`** evidencia, com saídas visuais, as camadas bronze e silver (volume de chegada dos dados, funil de limpeza e tabelas geradas). As estatísticas vêm do `src/pipeline_stats.py`.

## Tecnologias

| Camada        | Tecnologia                       | Por que foi escolhida                                          |
| ------------- | -------------------------------- | -------------------------------------------------------------- |
| Ingestão      | `datasus-dbc`, `dbfread`         | São as bibliotecas que leem `.dbc` sem precisar converter fora |
| Processamento | `pandas`, `numpy`                | Atende com folga o volume atual e o time já domina             |
| Armazenamento | Parquet via `pyarrow`            | Formato colunar e comprimido, bom para consultas analíticas    |
| Análise       | Jupyter, `matplotlib`, `seaborn` | Ferramentas usuais para exploração e gráficos estáticos        |
| Visualização interativa | `plotly`, `kaleido`    | Dashboard interativo (HTML auto-contido) e export de PNG       |

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
| CID da COVID   | O DATASUS usa `B342`, e não `U071` ou `U072`                  | A flag `is_covid` usa `B342`                                     |
| Escalas        | Variáveis numéricas em unidades diferentes                    | Colunas `*_norm` Min-Max em `[0, 1]`                             |
| Invariantes    | Nulos, duplicatas, período e intervalos de normalização       | `audit_quality` roda as asserções no fim do pipeline             |
