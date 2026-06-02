# Checklist AV2 do SUS Analytics

Estado das entregas da segunda avaliação (AV2), conforme a especificação da disciplina.

## Pipeline completo (arquitetura medalhão)

```text
Fontes:        (x) Finalizado   SIH/SUS (DATASUS), 48 arquivos .dbc
Ingestão:      (x) Finalizado   src/ingest_bronze.py  -> bronze
Armazenamento: (x) Finalizado   Parquet (bronze/silver) + CSV/Parquet (gold)
Transformação: (x) Finalizado   src/transform_silver.py  -> silver
Carregamento:  (x) Finalizado   src/build_gold.py  -> gold (5 tabelas)
Destino:       (x) Finalizado   output/dashboard.html + notebooks de análise
```

## Entrega principal: repositório GitHub como relatório

- [x] **README.md** estruturado como relatório: Introdução, Motivação, Objetivo,
      Metodologia (pipeline completo), Resultados e Visualizações, Conclusões.
- [x] Pasta `/src` com todos os scripts do pipeline.
- [x] Pasta `/notebooks` com os Jupyter Notebooks de análise.
- [x] Pasta `/data` com amostras pequenas versionadas (camada gold em CSV/Parquet).
- [x] Pasta `/docs` (documentação): arquitetura, checklists e divisão de tarefas.
- [x] Commits visíveis, com contribuição registrada de cada membro.

## Resultados, visualizações e storytelling

- [x] **Dashboard interativo** auto-contido: `output/dashboard.html` (Plotly, offline).
- [x] Figuras estáticas embutidas no relatório: `output/figuras/*.png`.
- [x] Análise com leitura crítica respondendo às 4 sub-perguntas:
      `notebooks/03_gold_analise.ipynb`.
- [x] **Evidências visuais das camadas bronze e silver** (atende ao feedback da AV1):
      `notebooks/00_pipeline_evidencias.ipynb`, como os dados chegaram, o que foi
      transformado (funil de limpeza) e quais tabelas foram geradas.

## Profundidade da análise

- [x] Série temporal mensal (volume e mortalidade), COVID frente a outros motivos.
- [x] Comparativo entre as ondas (volume, letalidade, UTI, permanência).
- [x] Perfil clínico COVID vs demais motivos.
- [x] Recorte demográfico (sexo e faixa etária) com taxa de óbito.
- [x] Concentração geográfica por município.

## Resposta ao feedback da AV1

| Ponto do feedback | Como foi endereçado |
| ----------------- | ------------------- |
| Faltaram saídas visuais nas camadas anteriores à gold | `notebooks/00_pipeline_evidencias.ipynb` mostra, com gráficos, o volume de chegada dos dados, o funil de limpeza bronze→silver e as tabelas geradas |
| Estrutura/organização do projeto pouco clara | README como relatório, diagrama do pipeline, este checklist e divisão de tarefas atualizada |
| Evidenciar o que foi transformado e quais arquivos/tabelas | Funil de etapas com contagem de linhas removidas + amostra de cada tabela gold |

## Preparação da apresentação final (até 20 min)

- [x] Dashboard interativo pronto para a demonstração ao vivo (abre offline no navegador).
- [ ] Roteiro da apresentação focado em resultados e na demonstração do pipeline em ação.
- [ ] Ensaiar a apresentação dentro do tempo.
