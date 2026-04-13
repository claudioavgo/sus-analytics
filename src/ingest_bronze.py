"""
ingest_bronze.py: camada bronze do pipeline SUS Analytics.

Lê os arquivos .dbc do SIH/SUS (SP, 2020 a 2023) e reúne todos eles em um
único Parquet bruto. Preserva os 113 campos originais e não aplica tipagem,
filtro ou seleção. Este é o primeiro passo da arquitetura medalhão.

Uso:
    python src/ingest_bronze.py

Saída:
    data/bronze/sihsus_sp_raw.parquet
"""

import os
import tempfile
import logging
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datasus_dbc import decompress
from dbfread import DBF

BRONZE_SOURCE_DIR = Path("../data/bronze/sihsus/SP")
BRONZE_OUTPUT = Path("../data/bronze/sihsus_sp_raw.parquet")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def list_dbc_files(directory: Path) -> list[Path]:
    files = sorted(directory.glob("*.dbc"))
    log.info("Encontrados %d arquivos .dbc em %s", len(files), directory)
    return files


def read_dbc_raw(dbc_path: Path) -> pd.DataFrame:
    """Descomprime um .dbc e devolve todos os campos em um DataFrame, sem tipagem."""
    with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        decompress(str(dbc_path), tmp_path)
        table = DBF(tmp_path, encoding="latin-1", load=True)
        df = pd.DataFrame(iter(table))
    finally:
        os.unlink(tmp_path)

    return df


def ingest_bronze(
    source_dir: Path = BRONZE_SOURCE_DIR,
    output: Path = BRONZE_OUTPUT,
) -> None:
    """Junta todos os .dbc em um único Parquet bruto na camada bronze."""
    output.parent.mkdir(parents=True, exist_ok=True)

    dbc_files = list_dbc_files(source_dir)
    if not dbc_files:
        raise FileNotFoundError(f"Nenhum arquivo .dbc encontrado em {source_dir}")

    frames = []
    for i, dbc_path in enumerate(dbc_files, 1):
        log.info("[%d/%d] Lendo %s", i, len(dbc_files), dbc_path.name)
        df = read_dbc_raw(dbc_path)
        df["_source_file"] = dbc_path.name
        frames.append(df)

    log.info("Consolidando %d DataFrames...", len(frames))
    consolidated = pd.concat(frames, ignore_index=True)
    log.info(
        "Total de registros: %d | Total de colunas: %d",
        len(consolidated),
        len(consolidated.columns),
    )

    table = pa.Table.from_pandas(consolidated)
    pq.write_table(table, output, compression="snappy")
    log.info("Bronze salvo em: %s (%.1f MB)", output, output.stat().st_size / 1e6)


if __name__ == "__main__":
    ingest_bronze()
