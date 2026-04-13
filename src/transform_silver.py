"""
transform_silver.py: camada bronze para silver no pipeline SUS Analytics.

Lê o Parquet bruto gerado pela bronze, seleciona os campos relevantes para
a pesquisa, aplica tipagem e filtros de qualidade, adiciona colunas derivadas
linha a linha (sem agregação) e salva o Parquet da silver.

Pergunta de pesquisa:
    "Como as ondas do COVID-19 impactaram o volume de internações
    e a mortalidade hospitalar no SUS-SP entre 2020 e 2023?"

Uso:
    python src/transform_silver.py

Pré-requisito:
    data/bronze/sihsus_sp_raw.parquet (gerado pelo src/ingest_bronze.py)

Saída:
    data/silver/sihsus_sp.parquet
"""

import logging
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

BRONZE_FILE = Path("../data/bronze/sihsus_sp_raw.parquet")
SILVER_FILE = Path("../data/silver/sihsus_sp.parquet")

# Campos selecionados do schema SIH/SUS (de 113 originais)
CAMPOS = [
    "ANO_CMPT",   # Ano de processamento
    "MES_CMPT",   # Mês de processamento
    "DT_INTER",   # Data de internação (aaaammdd)
    "DT_SAIDA",   # Data de saída (aaaammdd)
    "MUNIC_RES",  # Município de residência (cod. IBGE 6 dígitos)
    "MUNIC_MOV",  # Município do estabelecimento
    "DIAG_PRINC", # Diagnóstico principal (CID-10)
    "MORTE",      # Indicador de óbito (0 = Não, 1 = Sim)
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

# DATASUS/SIH-SUS registra COVID-19 como B342
COVID_CIDS = {"B342"}

ANO_INICIO = 2020
ANO_FIM = 2023

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def load_bronze(path: Path = BRONZE_FILE) -> pd.DataFrame:
    log.info("Lendo bronze: %s", path)
    df = pd.read_parquet(path)
    log.info("Registros carregados: %d | Colunas: %d", len(df), len(df.columns))
    return df


def select_fields(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in CAMPOS if c in df.columns]
    missing = set(CAMPOS) - set(cols)
    if missing:
        log.warning("Campos ausentes no bronze: %s", sorted(missing))
    log.info("Selecionando %d campos relevantes", len(cols))
    return df[cols].copy()


def _parse_datasus_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="%Y%m%d", errors="coerce")


def clean_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Tipagem das colunas: datas para datetime, numéricos para Int64/float, strings para upper e strip."""
    df["DT_INTER"] = _parse_datasus_date(df["DT_INTER"].astype(str))
    df["DT_SAIDA"] = _parse_datasus_date(df["DT_SAIDA"].astype(str))

    for col in ["MORTE", "DIAS_PERM", "UTI_MES_TO", "IDADE"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    df["VAL_TOT"] = pd.to_numeric(df["VAL_TOT"], errors="coerce")

    str_cols = ["ANO_CMPT", "MES_CMPT", "MUNIC_RES", "MUNIC_MOV",
                "DIAG_PRINC", "CAR_INT", "COMPLEX", "SEXO",
                "COD_IDADE", "CNES"]
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip().str.upper()
        df[col] = df[col].replace({"NAN": None, "NONE": None, "": None})

    return df


def drop_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Remove linhas com qualquer valor nulo nos 17 campos selecionados.

    A silver é garantida sem nulos. Qualquer linha com um campo faltante
    cai aqui, logo depois da tipagem.
    """
    before = len(df)
    nulls_por_col = df.isnull().sum().sort_values(ascending=False)
    nulls_por_col = nulls_por_col[nulls_por_col > 0]
    if not nulls_por_col.empty:
        log.info("Nulos por coluna antes do drop:\n%s", nulls_por_col.to_string())

    df = df.dropna(subset=list(df.columns)).copy()
    log.info(
        "Drop de nulos: %d -> %d (removidos: %d)",
        before, len(df), before - len(df),
    )
    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove linhas duplicadas em todas as 17 colunas."""
    before = len(df)
    df = df.drop_duplicates().copy()
    log.info(
        "Drop de duplicatas: %d -> %d (removidos: %d)",
        before, len(df), before - len(df),
    )
    return df


def filter_period(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["DT_INTER"].dt.year.between(ANO_INICIO, ANO_FIM)
    before = len(df)
    df = df[mask].copy()
    log.info(
        "Filtro de período (%d-%d): %d -> %d (removidos: %d)",
        ANO_INICIO, ANO_FIM, before, len(df), before - len(df),
    )
    return df


def add_covid_flag(df: pd.DataFrame) -> pd.DataFrame:
    df["is_covid"] = df["DIAG_PRINC"].isin(COVID_CIDS)
    n_covid = int(df["is_covid"].sum())
    log.info(
        "Internações por COVID identificadas: %d (%.1f%% do total)",
        n_covid, 100 * n_covid / len(df),
    )
    return df


def add_time_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["ano"] = df["DT_INTER"].dt.year.astype("Int64")
    df["mes"] = df["DT_INTER"].dt.month.astype("Int64")
    df["ano_mes"] = df["DT_INTER"].dt.to_period("M").dt.to_timestamp()
    return df


def add_age_group(df: pd.DataFrame) -> pd.DataFrame:
    """Converte IDADE e COD_IDADE em idade em anos e bucketiza por faixa etária.

    COD_IDADE no SIH/SUS:
        '2' = dias, '3' = meses, '4' = anos, '5' = anos a partir de 100.
    Dias e meses viram 0 anos (cai na faixa 0-4).
    O código '5' soma 100 à idade informada.
    """
    idade_anos = pd.Series(0, index=df.index, dtype="Int64")
    idade_anos = idade_anos.mask(df["COD_IDADE"] == "4", df["IDADE"])
    idade_anos = idade_anos.mask(df["COD_IDADE"] == "5", df["IDADE"] + 100)

    bins = [-1, 4, 14, 29, 44, 59, 74, 200]
    labels = ["0-4", "5-14", "15-29", "30-44", "45-59", "60-74", "75+"]
    df["faixa_etaria"] = pd.cut(
        idade_anos.astype("Float64"),
        bins=bins,
        labels=labels,
        right=True,
    ).astype(str)
    return df


NORMALIZE_COLS = ["DIAS_PERM", "UTI_MES_TO", "IDADE", "VAL_TOT"]


def normalize_min_max(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas `*_norm` com normalização Min-Max em [0, 1].

    As colunas originais ficam preservadas. A normalização ajuda a
    comparar variáveis em escalas diferentes, por exemplo VAL_TOT em
    reais frente a DIAS_PERM em dias.
    """
    for col in NORMALIZE_COLS:
        s = df[col].astype("float64")
        mn, mx = s.min(), s.max()
        if mx > mn:
            df[f"{col}_norm"] = ((s - mn) / (mx - mn)).astype("float64")
        else:
            df[f"{col}_norm"] = 0.0
        log.info(
            "Normalizado %s -> %s_norm (min=%.2f, max=%.2f)",
            col, col, mn, mx,
        )
    return df


def audit_quality(df: pd.DataFrame) -> None:
    """Auditoria de qualidade: asserções de invariante e resumo estatístico.

    Roda as asserções que devem valer em qualquer silver saudável e
    loga um relatório de qualidade. Se alguma invariante falha, o
    pipeline para e nada é gravado.
    """
    log.info("=== AUDITORIA DE QUALIDADE DA SILVER ===")

    total_nulos = int(df.isnull().sum().sum())
    total_dups = int(df.duplicated().sum())
    log.info("Linhas:        %d", len(df))
    log.info("Colunas:       %d", len(df.columns))
    log.info("Total nulos:   %d", total_nulos)
    log.info("Duplicatas:    %d", total_dups)

    periodo_ok = df["DT_INTER"].dt.year.between(ANO_INICIO, ANO_FIM).all()
    log.info(
        "Período %d-%d: %s a %s (ok=%s)",
        ANO_INICIO, ANO_FIM,
        df["DT_INTER"].min().date(),
        df["DT_INTER"].max().date(),
        bool(periodo_ok),
    )

    for col in NORMALIZE_COLS:
        norm_col = f"{col}_norm"
        log.info(
            "%-10s  min=%-12.2f max=%-12.2f  |  %s min=%.4f max=%.4f",
            col, float(df[col].min()), float(df[col].max()),
            norm_col, float(df[norm_col].min()), float(df[norm_col].max()),
        )

    log.info("Dtypes finais:\n%s", df.dtypes.to_string())

    assert total_nulos == 0, f"Silver possui {total_nulos} nulos"
    assert total_dups == 0, f"Silver possui {total_dups} duplicatas"
    assert periodo_ok, "Silver possui datas fora do período 2020-2023"
    for col in NORMALIZE_COLS:
        norm = df[f"{col}_norm"]
        assert norm.min() >= 0 and norm.max() <= 1, f"{col}_norm fora de [0,1]"

    log.info("Auditoria OK: silver aprovada.")


def transform_silver(
    bronze_path: Path = BRONZE_FILE,
    output: Path = SILVER_FILE,
) -> pd.DataFrame:
    """Executa o pipeline bronze para silver do início ao fim."""
    output.parent.mkdir(parents=True, exist_ok=True)

    df = load_bronze(bronze_path)
    df = select_fields(df)
    df = clean_dtypes(df)
    df = drop_nulls(df)
    df = drop_duplicates(df)
    df = filter_period(df)
    df = add_covid_flag(df)
    df = add_time_columns(df)
    df = add_age_group(df)
    df = normalize_min_max(df)
    audit_quality(df)

    table = pa.Table.from_pandas(df)
    pq.write_table(table, output, compression="snappy")
    log.info("Silver salvo em: %s (%.1f MB)", output, output.stat().st_size / 1e6)

    _log_summary(df)
    return df


def _log_summary(df: pd.DataFrame) -> None:
    log.info("--- Resumo da tabela silver ---")
    log.info("Total de internações: %d", len(df))
    log.info("Internações COVID: %d", int(df["is_covid"].sum()))
    log.info("Óbitos totais: %d", int(df["MORTE"].sum()))
    log.info("Óbitos COVID: %d", int(df.loc[df["is_covid"], "MORTE"].sum()))
    log.info(
        "Período: %s a %s",
        df["DT_INTER"].min().date(),
        df["DT_INTER"].max().date(),
    )
    log.info("Colunas: %s", list(df.columns))


if __name__ == "__main__":
    transform_silver()
