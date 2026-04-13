# Checklist AV1 — SUS Analytics

Status atual das etapas obrigatórias do pipeline de dados para a primeira entrega.

## Status do pipeline

| Etapa           | Status        | Observações                                                                 |
| --------------- | ------------- | --------------------------------------------------------------------------- |
| Ingestão        | ✅ Finalizado | `src/ingest_bronze.py` consolida os 48 `.dbc` em Parquet bruto              |
| Armazenamento   | ✅ Finalizado | Bronze e Silver persistidas em Parquet (`pyarrow`, compressão snappy)       |
| Transformação   | ✅ Finalizado | `src/transform_silver.py` aplica tipagem, filtros e enriquecimento          |

## Minientregas AV1

- [x] Documento de Arquitetura — `docs/arquitetura_dados.md`
- [x] Repositório GitHub estruturado (`/src`, `/data`, `/notebooks`, `/docs`)
- [x] README com nome, descrição, fonte dos dados e ferramentas
- [x] Demonstração técnica — `notebooks/01_exploracao_sihsus.ipynb`
- [x] Visualização das variáveis da silver — `notebooks/02_silver_visualizacoes.ipynb`
- [x] Checklist preenchido (este arquivo)
- [ ] Exportar `arquitetura_dados.md` para PDF/DOCX antes da apresentação
- [ ] Garantir commits visíveis de cada membro da equipe

## Fora do escopo da AV1

- Camada Gold (agregações e tabelas analíticas) — planejada para AV2
- Análises consolidadas (mortalidade por onda, perfil UTI, impacto regional) — AV2
