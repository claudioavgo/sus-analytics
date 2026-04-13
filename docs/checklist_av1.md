# Checklist AV1 do SUS Analytics

Estado atual das etapas obrigatórias do pipeline de dados para a primeira entrega.

## Status do pipeline (formato oficial AV1)

```text
Ingestão:      ( ) Em progresso  (x) Finalizado  ( ) Pendente
Armazenamento: ( ) Em progresso  (x) Finalizado  ( ) Pendente
Transformação: ( ) Em progresso  (x) Finalizado  ( ) Pendente
```

## Detalhamento

| Etapa         | Status        | Observações                                                              |
| ------------- | ------------- | ------------------------------------------------------------------------ |
| Ingestão      | ✅ Finalizado | `src/ingest_bronze.py` reúne os 48 `.dbc` em um Parquet bruto            |
| Armazenamento | ✅ Finalizado | Bronze e silver salvas em Parquet (`pyarrow`, compressão snappy)         |
| Transformação | ✅ Finalizado | `src/transform_silver.py` aplica tipagem, filtros e enriquecimento       |

## Minientregas AV1

- [x] Documento de arquitetura: `docs/arquitetura_dados.md` e `docs/arquitetura_dados.docx`
- [x] Repositório GitHub estruturado (`/src`, `/data`, `/notebooks`, `/docs`)
- [x] README com nome, descrição, fonte dos dados e ferramentas utilizadas
- [x] Demonstração técnica: `notebooks/01_exploracao_sihsus.ipynb`
- [x] Visualização das variáveis da silver: `notebooks/02_silver_visualizacoes.ipynb`
- [x] Checklist preenchido (este arquivo)
- [x] Documento de arquitetura também em DOCX (`docs/arquitetura_dados.docx`)
- [x] Commits visíveis de cada membro da equipe (Bruno, Cláudio e Vinícius)

## Fora do escopo da AV1

- Camada gold, com as tabelas agregadas e analíticas, fica para a AV2.
- Análises consolidadas (mortalidade por onda, perfil de UTI, impacto regional) também ficam para a AV2.

