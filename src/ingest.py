"""
ingest.py — Camada Bronze -> Silver

Lê os arquivos .dbc do SIH/SUS (SP, 2020-2023), seleciona os campos relevantes
para a pesquisa sobre impacto do COVID-19 e exporta um arquivo Parquet consolidado.

Uso:
    python src/ingest.py

Saida:
    data/silver/sihsus_sp.parquet
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

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BRONZE_DIR = Path("data/bronze/sihsus/SP")
SILVER_DIR = Path("data/silver")
OUTPUT_FILE = SILVER_DIR / "sihsus_sp.parquet"

# Campos selecionados do schema SIH/SUS (113 campos no total)
# Apenas o necessário para responder a pergunta de pesquisa
CAMPOS = [
    "ANO_CMPT",   # Ano de processamento
    "MES_CMPT",   # Mês de processamento
    "DT_INTER",   # Data de internação (aaaammdd)
    "DT_SAIDA",   # Data de saída (aaaammdd)
    "MUNIC_RES",  # Município de residência (cod. IBGE 6 dígitos)
    "MUNIC_MOV",  # Município do estabelecimento
    "DIAG_PRINC", # Diagnóstico principal (CID-10)
    "MORTE",      # Indicador de óbito (0=Nao, 1=Sim)
    "DIAS_PERM",  # Dias de permanência
    "UTI_MES_TO", # Dias de UTI no mês
    "CAR_INT",    # Caráter da internação (eletiva/urgência)
    "COMPLEX",    # Nível de complexidade
    "SEXO",       # Sexo do paciente
    "IDADE",      # Idade do paciente
    "COD_IDADE",  # Unidade de medida da idade (4=Anos)
    "VAL_TOT",    # Valor total da AIH (R$)
    "CNES",       # Código CNES do estabelecimento
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------------

def list_dbc_files(directory: Path) -> list[Path]:
    """Retorna todos os arquivos .dbc do diretório, ordenados."""
    files = sorted(directory.glob("*.dbc"))
    log.info("Encontrados %d arquivos .dbc em %s", len(files), directory)
    return files


def read_dbc(dbc_path: Path) -> pd.DataFrame:
    """
    Descomprime um arquivo .dbc e lê os campos selecionados como DataFrame.

    Args:
        dbc_path: Caminho para o arquivo .dbc.

    Returns:
        DataFrame com os campos definidos em CAMPOS (subset disponível).
    """
    with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        decompress(str(dbc_path), tmp_path)
        table = DBF(tmp_path, encoding="latin-1", load=True)
        records = [
            {campo: rec.get(campo) for campo in CAMPOS}
            for rec in table
        ]
        df = pd.DataFrame(records)
    finally:
        os.unlink(tmp_path)

    return df


def _parse_datasus_date(series: pd.Series) -> pd.Series:
    """Converte campo de data no formato aaaammdd (str) para datetime."""
    return pd.to_datetime(series, format="%Y%m%d", errors="coerce")


def clean_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica tipagem correta ao DataFrame lido do DBF.

    - Datas: DT_INTER, DT_SAIDA -> datetime
    - Numéricos: MORTE, DIAS_PERM, UTI_MES_TO, IDADE, VAL_TOT -> tipos corretos
    - Strings: demais campos -> str, com strip de espacos extras
    """
    # Datas
    df["DT_INTER"] = _parse_datasus_date(df["DT_INTER"].astype(str))
    df["DT_SAIDA"] = _parse_datasus_date(df["DT_SAIDA"].astype(str))

    # Inteiros
    for col in ["MORTE", "DIAS_PERM", "UTI_MES_TO", "IDADE"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Float
    df["VAL_TOT"] = pd.to_numeric(df["VAL_TOT"], errors="coerce")

    # Strings — strip e uppercase
    str_cols = ["ANO_CMPT", "MES_CMPT", "MUNIC_RES", "MUNIC_MOV",
                "DIAG_PRINC", "CAR_INT", "COMPLEX", "SEXO",
                "COD_IDADE", "CNES"]
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip().str.upper()
        df[col] = df[col].replace({"NAN": None, "NONE": None, "": None})

    return df


def ingest(bronze_dir: Path = BRONZE_DIR, output: Path = OUTPUT_FILE) -> None:
    """
    Executa a ingestão completa: lê todos os .dbc, consolida e salva em Parquet.

    Args:
        bronze_dir: Diretório com os arquivos .dbc.
        output: Caminho do arquivo Parquet de saída.
    """
    output.parent.mkdir(parents=True, exist_ok=True)

    dbc_files = list_dbc_files(bronze_dir)
    if not dbc_files:
        raise FileNotFoundError(f"Nenhum arquivo .dbc encontrado em {bronze_dir}")

    frames = []
    for i, dbc_path in enumerate(dbc_files, 1):
        log.info("[%d/%d] Lendo %s", i, len(dbc_files), dbc_path.name)
        df = read_dbc(dbc_path)
        df = clean_dtypes(df)
        df["_source_file"] = dbc_path.name
        frames.append(df)

    log.info("Consolidando %d DataFrames...", len(frames))
    consolidated = pd.concat(frames, ignore_index=True)

    log.info(
        "Total de registros: %d | Período: %s a %s",
        len(consolidated),
        consolidated["DT_INTER"].min().date() if consolidated["DT_INTER"].notna().any() else "?",
        consolidated["DT_INTER"].max().date() if consolidated["DT_INTER"].notna().any() else "?",
    )

    table = pa.Table.from_pandas(consolidated)
    pq.write_table(table, output, compression="snappy")
    log.info("Silver salvo em: %s (%.1f MB)", output, output.stat().st_size / 1e6)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ingest()
