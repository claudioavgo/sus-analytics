# Divisão de tarefas do SUS Analytics

**Disciplina:** Fundamentos de Big Data
**Equipe:** Bruno Ribeiro, Cláudio Alves e Vinícius Ventura

## Responsabilidades por membro

| Membro           | Responsabilidades                                                              |
| ---------------- | ------------------------------------------------------------------------------ |
| Bruno Ribeiro    | Pipeline bronze para silver, scripts em Python e decisões de arquitetura       |
| Vinícius Ventura | Notebook de análise, visualizações exploratórias e apoio na redação            |
| Cláudio Alves    | README, documentação técnica, checklist e preparação da apresentação em aula   |

## Divisão por fase

### AV1 (13/04)

| Tarefa                                 | Responsável                      | Status    |
| -------------------------------------- | -------------------------------- | --------- |
| Download e organização dos dados `.dbc`| Bruno Ribeiro e Vinícius Ventura | Concluído |
| Implementação do `src/ingest_bronze.py`| Bruno Ribeiro e Vinícius Ventura | Concluído |
| Implementação do `src/transform_silver.py` | Bruno Ribeiro e Vinícius Ventura | Concluído |
| Notebook de demonstração técnica       | Bruno Ribeiro e Vinícius Ventura | Concluído |
| Documentação de arquitetura            | Cláudio Alves                    | Concluído |
| Dicionário de dados                    | Cláudio Alves                    | Concluído |
| README e checklist da AV1              | Cláudio Alves                    | Concluído |

### AV2 (08/06)

| Tarefa                                          | Responsável                      | Status    |
| ----------------------------------------------- | -------------------------------- | --------- |
| Camada gold (`src/build_gold.py`)               | Bruno Ribeiro e Vinícius Ventura | Concluído |
| Estatísticas de evidência (`src/pipeline_stats.py`) | Bruno Ribeiro                | Concluído |
| Dashboard interativo (`src/build_dashboard.py`) | Vinícius Ventura                 | Concluído |
| Notebook de análise da gold (03)                | Vinícius Ventura                 | Concluído |
| Modelo probabilístico de óbito (`src/build_model.py` + notebook 04) | Bruno Ribeiro e Vinícius Ventura | Concluído |
| Notebook de evidências do pipeline (00)         | Bruno Ribeiro                    | Concluído |
| README como relatório e checklist da AV2        | Cláudio Alves                    | Concluído |
| Atualização da documentação de arquitetura      | Cláudio Alves                    | Concluído |
| Preparação da apresentação final                | Cláudio Alves                    | Em andamento |
