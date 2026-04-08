# SUS Analytics

Analise da distribuicao de internacoes hospitalares no Brasil pelo SUS, investigando variacoes regionais, tendencias temporais e a associacao com fatores socioeconomicos como populacao e renda.

## Pergunta de pesquisa

Como as internacoes hospitalares no Brasil se distribuem entre regioes e ao longo do tempo, e em que medida fatores socioeconomicos estao associados a maiores taxas de hospitalizacao no SUS?

## Fontes de dados

| Fonte | Descricao | Formato |
|-------|-----------|---------|
| SIH/SUS (DATASUS) | Registros de internacoes hospitalares (AIH Reduzida) | `.dbc` |
| IBGE | Estimativas populacionais por municipio | `.dbf` |
| IBGE | PIB dos Municipios (proxy de renda) | `.xlsx` |

Os dados brutos estao organizados em `data/bronze/`, seguindo uma arquitetura medalhao (bronze/silver/gold).

## Estrutura do projeto

```
data/
  bronze/
    sihsus/             # AIH Reduzida por UF - todas as 27 UFs, 2020-2023
    ibge/               # Populacao residente por municipio - 2020 a 2022
      pib_municipios/   # PIB municipal - 2010 a 2023
scripts/
  download_sihsus.ps1   # Script de download automatizado dos dados SIHSUS
```

## Cobertura

- **Periodo:** 2020-2023 (todos os meses)
- **Estados:** Todas as 27 UFs
- **Dados socioeconomicos:** PIB municipal 2010-2023, populacao 2020-2022

## Licenca

Dados publicos disponibilizados pelo DATASUS e IBGE.
