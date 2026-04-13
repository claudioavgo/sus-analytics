"""
transform.py — Camada Silver -> Gold

Lê o Parquet consolidado da silver, aplica transformacoes analíticas
e gera a tabela gold pronta para responder a pergunta de pesquisa:

    "Como as ondas do COVID-19 impactaram o volume de internações
    e a mortalidade hospitalar no SUS-SP entre 2020 e 2023?"

Uso:
    python src/transform.py

Pre-requisito:
    data/silver/sihsus_sp.parquet (gerado por src/ingest.py)

Saída:
    data/gold/internacoes_covid_sp.parquet
"""

import logging
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

SILVER_FILE = Path("data/silver/sihsus_sp.parquet")
GOLD_DIR = Path("data/gold")
OUTPUT_FILE = GOLD_DIR / "internacoes_covid_sp.parquet"

# O sistema DATASUS utiliza B342 para registrar internações por COVID-19
COVID_CIDS = {"B342"}

# Período de análise
ANO_INICIO = 2020
ANO_FIM = 2023

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Funções de transformação
# ---------------------------------------------------------------------------


def load_silver(path: Path = SILVER_FILE) -> pd.DataFrame:
    """Lê o arquivo Parquet da camada silver."""
    log.info("Lendo silver: %s", path)
    df = pd.read_parquet(path)
    log.info("Registros carregados: %d", len(df))
    return df


def filter_period(df: pd.DataFrame) -> pd.DataFrame:
    """Remove registros fora do período 2020-2023 com base em DT_INTER."""
    mask = df["DT_INTER"].dt.year.between(ANO_INICIO, ANO_FIM)
    before = len(df)
    df = df[mask].copy()
    log.info(
        "Filtro de período: %d -> %d registros (removidos: %d)",
        before,
        len(df),
        before - len(df),
    )
    return df


def remove_invalid_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove registros com data de internação inválida (NaT)."""
    before = len(df)
    df = df[df["DT_INTER"].notna()].copy()
    log.info(
        "Remocao de datas invalidas: %d -> %d registros (removidos: %d)",
        before,
        len(df),
        before - len(df),
    )
    return df


def add_covid_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona coluna booleana `is_covid` indicando se o diagnóstico
    principal e COVID-19 (CID B342 — código utilizado pelo DATASUS/SIH-SUS).
    """
    df["is_covid"] = df["DIAG_PRINC"].isin(COVID_CIDS)
    n_covid = df["is_covid"].sum()
    log.info(
        "Internações por COVID identificadas: %d (%.1f%% do total)",
        n_covid,
        100 * n_covid / len(df),
    )
    return df


def add_time_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona colunas derivadas de tempo para facilitar agregações:
    - ano: ano de internação
    - mês: mês de internação (1-12)
    - ano_mes: primeiro dia do mês (para serie temporal)
    """
    df["ano"] = df["DT_INTER"].dt.year.astype("Int64")
    df["mes"] = df["DT_INTER"].dt.month.astype("Int64")
    df["ano_mes"] = df["DT_INTER"].dt.to_period("M").dt.to_timestamp()
    return df


def add_age_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona coluna `faixa_etaria` com categorias para análise demográfica.
    Considera apenas registros com COD_IDADE == '4' (anos completos).
    """
    bins = [0, 4, 14, 29, 44, 59, 74, 150]
    labels = ["0-4", "5-14", "15-29", "30-44", "45-59", "60-74", "75+"]

    idade_em_anos = df["IDADE"].where(df["COD_IDADE"] == "4", other=pd.NA)
    df["faixa_etaria"] = pd.cut(
        idade_em_anos.astype("Float64"),
        bins=bins,
        labels=labels,
        right=True,
    )
    return df


def transform(
    silver_path: Path = SILVER_FILE,
    output: Path = OUTPUT_FILE,
) -> pd.DataFrame:
    """
    Executa o pipeline completo de transformação silver -> gold.

    Args:
        silver_path: Caminho do Parquet silver.
        output: Caminho de saída do Parquet gold.

    Returns:
        DataFrame gold (também salvo em disco).
    """
    output.parent.mkdir(parents=True, exist_ok=True)

    df = load_silver(silver_path)
    df = remove_invalid_dates(df)
    df = filter_period(df)
    df = add_covid_flag(df)
    df = add_time_columns(df)
    df = add_age_group(df)

    # Remove coluna auxiliar de rastreamento da ingestão
    df = df.drop(columns=["_source_file"], errors="ignore")

    table = pa.Table.from_pandas(df)
    pq.write_table(table, output, compression="snappy")
    log.info("Gold salvo em: %s (%.1f MB)", output, output.stat().st_size / 1e6)

    _log_summary(df)
    return df


def _log_summary(df: pd.DataFrame) -> None:
    """Imprime um resumo da tabela gold para validação rapida."""
    log.info("--- Resumo da tabela gold ---")
    log.info("Total de internações: %d", len(df))
    log.info("Internações COVID: %d", df["is_covid"].sum())
    log.info("Óbitos totais: %d", df["MORTE"].sum())
    log.info("Óbitos COVID: %d", df.loc[df["is_covid"], "MORTE"].sum())
    log.info(
        "Período: %s a %s",
        df["DT_INTER"].min().date(),
        df["DT_INTER"].max().date(),
    )
    log.info("Colunas: %s", list(df.columns))

if __name__ == "__main__":
    transform()
