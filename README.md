# SUS Analytics

Analise da distribuicao de internacoes hospitalares no Brasil pelo SUS, investigando variacoes regionais, tendencias temporais e a associacao com fatores socioeconomicos como populacao e renda.

## Pergunta de pesquisa

Como as internacoes hospitalares no Brasil se distribuem entre regioes e ao longo do tempo, e em que medida fatores socioeconomicos estao associados a maiores taxas de hospitalizacao no SUS?

## Fontes de dados

| Fonte | Descricao | Formato |
|-------|-----------|---------|
| SIH/SUS (DATASUS) | Registros de internacoes hospitalares (AIH Reduzida) | `.dbc` |
| IBGE | Estimativas populacionais por municipio | `.dbf` |

Os dados brutos estao organizados em `data/bronze/`, seguindo uma arquitetura medalhao (bronze/silver/gold).

## Estrutura do projeto

```
data/
  bronze/
    sihsus/       # AIH Reduzida por UF (AM, BA, CE, MG, RJ, SP) - 2020 a 2022
    ibge/          # Populacao residente por municipio - 2020 a 2022
```

## Cobertura

- **Periodo:** 2020-2022 (meses selecionados: janeiro, junho, dezembro)
- **Estados:** AM, BA, CE, MG, RJ, SP

## Licenca

Dados publicos disponibilizados pelo DATASUS e IBGE.
