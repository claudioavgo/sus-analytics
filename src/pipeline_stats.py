"""
pipeline_stats.py: estatísticas de evidência do pipeline (bronze e silver).

Reaproveita as funções da transformação (transform_silver) e registra, etapa
a etapa, quantas linhas entraram e quantas sobraram. Também mede o volume de
internações que chegou em cada arquivo mensal da bronze. Salva tudo em CSVs
pequenos na camada gold, que o notebook de evidências (00) visualiza sem
precisar recarregar os Parquets pesados.

Este script existe para responder, com saídas visuais, à pergunta "como os
dados chegaram, o que foi transformado e quais tabelas foram geradas".

Uso:
    python src/pipeline_stats.py

Pré-requisito:
    data/bronze/sihsus_sp_raw.parquet (gerado pelo src/ingest_bronze.py)

Saída:
    data/gold/pipeline_funnel.csv          linhas a cada etapa bronze -> silver
    data/gold/pipeline_volume_mensal.csv   internações por arquivo mensal (bronze)
"""

import logging
from pathlib import Path

import pandas as pd

from transform_silver import (
    BRONZE_FILE,
    select_fields,
    clean_dtypes,
    drop_nulls,
    drop_duplicates,
    filter_period,
)

GOLD_DIR = Path("../data/gold")
FUNNEL_CSV = GOLD_DIR / "pipeline_funnel.csv"
VOLUME_CSV = GOLD_DIR / "pipeline_volume_mensal.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def _parse_competencia(source_file: str) -> str:
    """Extrai a competência (AAAA-MM) do nome RDSPyymm.dbc da bronze."""
    base = source_file.upper().replace("RDSP", "").replace(".DBC", "")
    if len(base) >= 4 and base[:4].isdigit():
        ano = 2000 + int(base[:2])
        mes = int(base[2:4])
        return f"{ano}-{mes:02d}"
    return "desconhecida"


def build_volume_mensal(df_bronze: pd.DataFrame) -> pd.DataFrame:
    """Volume de registros por arquivo mensal da bronze (como os dados chegaram)."""
    if "_source_file" not in df_bronze.columns:
        log.warning("Coluna _source_file ausente na bronze; volume mensal vazio.")
        return pd.DataFrame(columns=["competencia", "registros"])
    vol = (df_bronze["_source_file"].map(_parse_competencia)
           .value_counts().rename_axis("competencia").reset_index(name="registros"))
    vol = vol.sort_values("competencia").reset_index(drop=True)
    log.info("volume mensal: %d competências", len(vol))
    return vol


def build_funnel(df_bronze: pd.DataFrame) -> pd.DataFrame:
    """Funil de linhas: quantas sobram a cada etapa da transformação silver."""
    etapas = []
    etapas.append(("Bronze bruto", len(df_bronze)))

    df = select_fields(df_bronze)
    df = clean_dtypes(df)
    etapas.append(("Após tipagem", len(df)))

    df = drop_nulls(df)
    etapas.append(("Após remover nulos", len(df)))

    df = drop_duplicates(df)
    etapas.append(("Após remover duplicatas", len(df)))

    df = filter_period(df)
    etapas.append(("Silver (2020–2023)", len(df)))

    funnel = pd.DataFrame(etapas, columns=["etapa", "linhas"])
    funnel["removidas_na_etapa"] = (-funnel["linhas"].diff()).fillna(0).astype(int)
    funnel["pct_do_bronze"] = (100 * funnel["linhas"] / len(df_bronze)).round(2)
    log.info("funil de etapas:\n%s", funnel.to_string(index=False))
    return funnel


def build_pipeline_stats(bronze_path: Path = BRONZE_FILE, gold_dir: Path = GOLD_DIR) -> dict:
    gold_dir.mkdir(parents=True, exist_ok=True)
    log.info("Lendo bronze: %s", bronze_path)
    df_bronze = pd.read_parquet(bronze_path)
    log.info("Bronze: %d linhas x %d colunas", len(df_bronze), len(df_bronze.columns))

    volume = build_volume_mensal(df_bronze)
    funnel = build_funnel(df_bronze)

    volume.to_csv(VOLUME_CSV, index=False, encoding="utf-8")
    funnel.to_csv(FUNNEL_CSV, index=False, encoding="utf-8")
    log.info("Salvos: %s e %s", FUNNEL_CSV.name, VOLUME_CSV.name)
    return {"volume_mensal": volume, "funnel": funnel}


if __name__ == "__main__":
    build_pipeline_stats()
