# Arquitetura de Dados

## Visao geral

O projeto segue a arquitetura medalhao (bronze/silver/gold) para organizar o fluxo de dados desde a ingestao bruta ate as tabelas analiticas.

```
data/
  bronze/          Dados brutos, exatamente como obtidos das fontes
  silver/          Dados limpos, tipados e padronizados (a implementar)
  gold/            Dados agregados e prontos para analise (a implementar)
```

## Camada Bronze (implementada)

Dados brutos sem nenhuma transformacao.

```
data/bronze/
  sihsus/
    AC/RDAC2001.dbc ... RDAC2312.dbc    # 48 arquivos por UF
    AL/ ...
    ... (27 UFs)
    TO/
    docs/IT_SIHSUS_1603.pdf             # Layout oficial do DATASUS
  ibge/
    POPTBR20.dbf                        # Populacao 2020
    POPTBR21.dbf                        # Populacao 2021
    POPTBR22.dbf                        # Populacao 2022 (duplicado)
    POPTBR22/*.dbf                      # Populacao 2022 por UF
    pib_municipios/
      PIB dos Municipios - base de dados 2010-2023.xlsx
    docs/*.pdf                          # Documentacao IBGE
```

### Volumes

| Fonte | Arquivos | Tamanho | Formato |
|-------|----------|---------|---------|
| SIH/SUS | 1.296 | ~3.4 GB | .dbc (DBF comprimido) |
| Populacao IBGE | 31 | ~5 MB | .dbf |
| PIB Municipal | 1 | ~21 MB | .xlsx |

## Camada Silver (a implementar)

Dados limpos e padronizados. Transformacoes esperadas:

### SIH/SUS
- Descompressao .dbc -> leitura dos campos relevantes
- Selecao de colunas uteis para a pesquisa
- Tipagem correta (datas, numericos, categoricos)
- Padronizacao do codigo de municipio para 6 digitos

### Populacao IBGE
- Deduplicacao do arquivo 2022
- Padronizacao do codigo de municipio para 6 digitos
- Validacao de consistencia entre arquivos anuais e por UF

### PIB Municipal
- Selecao de colunas relevantes (identificacao + campos economicos)
- Truncagem do codigo de municipio de 7 para 6 digitos
- Filtragem do periodo 2020-2023

## Camada Gold (a implementar)

Tabelas analiticas prontas para responder a pergunta de pesquisa:

- **Internacoes por municipio/mes:** contagem de AIHs, dias de permanencia, valor total
- **Taxa de hospitalizacao:** internacoes / populacao por municipio
- **Tabela analitica unificada:** municipio x ano com taxa de internacao, PIB per capita, populacao

## Qualidade dos dados

| Problema | Base | Descricao |
|----------|------|-----------|
| Duplicacao | POPTBR22.dbf | 11.140 registros para 5.570 municipios |
| Codigo municipio | Todas | DATASUS usa 6 digitos, IBGE PIB usa 7 digitos |
| Campos zerados | SIH/SUS | ~19 campos legados sem conteudo |
| VAB incompleto | PIB 2022-2023 | Desagregacao setorial indisponivel |
| Populacao 2023 | Populacao | Nao disponivel nos arquivos atuais |
