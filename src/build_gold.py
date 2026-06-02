"""
build_gold.py: camada silver para gold no pipeline SUS Analytics.

Lê o Parquet da silver (granular, uma linha por AIH) e gera as tabelas
agregadas da camada gold, prontas para responder à pergunta de pesquisa.
Cada tabela é salva em dois formatos: Parquet (consumo analítico) e CSV
(amostra versionável em /dados e fácil de abrir em qualquer ferramenta).

Pergunta de pesquisa:
    "Como as ondas da COVID-19 impactaram o volume de internações
    e a mortalidade hospitalar no SUS-SP entre 2020 e 2023?"

Tabelas geradas (data/gold/):
    serie_mensal              Série temporal mensal: volume e mortalidade.
    ondas                     Consolidado por onda da pandemia.
    perfil_covid_vs_outros    Perfil clínico COVID frente a outros motivos.
    demografia_covid          Internações e óbitos COVID por sexo e faixa.
    municipios_covid          Top municípios por internação COVID.

Uso:
    python src/build_gold.py

Pré-requisito:
    data/silver/sihsus_sp.parquet (gerado pelo src/transform_silver.py)
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

SILVER_FILE = Path("../data/silver/sihsus_sp.parquet")
GOLD_DIR = Path("../data/gold")

# Janelas das ondas, definidas a partir dos picos observados na própria
# série mensal de internações por COVID (CID B342) em São Paulo. Não são
# datas arbitrárias: cada janela vai de um vale ao vale seguinte da série.
#
#   Onda 1 (vírus original) ... pico em Jul/2020 (~20,8 mil internações)
#   Onda 2 (variante Gama) ..... pico em Mar/2021 (~45,2 mil internações)
#   Onda 3 (variante Ômicron) .. pico em Jan/2022 (~14,1 mil internações)
#   Período endêmico ........... cauda da série, sem picos relevantes
ONDAS = [
    ("Onda 1 (original)", "2020-01-01", "2020-10-31"),
    ("Onda 2 (Gama)", "2020-11-01", "2021-10-31"),
    ("Onda 3 (Ômicron)", "2021-11-01", "2022-04-30"),
    ("Endêmico", "2022-05-01", "2023-12-31"),
]

# SIH/SUS registra sexo como 1 = Masculino, 3 = Feminino.
MAPA_SEXO = {"1": "Masculino", "3": "Feminino"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def load_silver(path: Path = SILVER_FILE) -> pd.DataFrame:
    log.info("Lendo silver: %s", path)
    df = pd.read_parquet(path)
    log.info("Registros carregados: %d | Colunas: %d", len(df), len(df.columns))
    return df


def add_onda(df: pd.DataFrame) -> pd.DataFrame:
    """Rotula cada internação com a onda da pandemia em que ela caiu.

    A classificação usa a data de internação (DT_INTER) e as janelas
    definidas em ONDAS. Internações fora de todas as janelas ficam com
    rótulo "Fora das ondas" (não devem existir no recorte 2020-2023).
    """
    df = df.copy()
    df["onda"] = "Fora das ondas"
    for nome, inicio, fim in ONDAS:
        mask = df["DT_INTER"].between(pd.Timestamp(inicio), pd.Timestamp(fim))
        df.loc[mask, "onda"] = nome
    fora = int((df["onda"] == "Fora das ondas").sum())
    if fora:
        log.warning("Internações fora das janelas de onda: %d", fora)
    return df


def build_serie_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Série temporal mensal: volume e mortalidade, COVID frente a outros.

    Responde à pergunta sobre a evolução mês a mês do volume de
    internações e da taxa de óbito hospitalar.
    """
    grp = df.groupby("ano_mes")
    out = pd.DataFrame({
        "internacoes_total": grp.size(),
        "internacoes_covid": grp["is_covid"].sum(),
        "obitos_total": grp["MORTE"].sum(),
        "obitos_covid": grp.apply(
            lambda g: int(g.loc[g["is_covid"], "MORTE"].sum()), include_groups=False
        ),
    }).reset_index()

    out["internacoes_outros"] = out["internacoes_total"] - out["internacoes_covid"]
    out["obitos_outros"] = out["obitos_total"] - out["obitos_covid"]
    out["taxa_obito_total"] = 100 * out["obitos_total"] / out["internacoes_total"]
    out["taxa_obito_covid"] = 100 * out["obitos_covid"] / out["internacoes_covid"].replace(0, np.nan)
    out["taxa_obito_outros"] = 100 * out["obitos_outros"] / out["internacoes_outros"]

    cols = [
        "ano_mes", "internacoes_total", "internacoes_covid", "internacoes_outros",
        "obitos_total", "obitos_covid", "obitos_outros",
        "taxa_obito_total", "taxa_obito_covid", "taxa_obito_outros",
    ]
    out = out[cols]
    taxa_cols = ["taxa_obito_total", "taxa_obito_covid", "taxa_obito_outros"]
    out[taxa_cols] = out[taxa_cols].round(2)
    log.info("serie_mensal: %d meses", len(out))
    return out


def build_ondas(df: pd.DataFrame) -> pd.DataFrame:
    """Consolidado por onda: foca nas internações COVID de cada janela.

    Mostra como volume, mortalidade e gravidade (UTI, permanência) mudaram
    de uma onda para a outra.
    """
    covid = df[df["is_covid"]].copy()
    grp = covid.groupby("onda")

    out = pd.DataFrame({
        "internacoes_covid": grp.size(),
        "obitos_covid": grp["MORTE"].sum(),
        "taxa_obito_covid": 100 * grp["MORTE"].mean(),
        "dias_perm_medio": grp["DIAS_PERM"].mean(),
        "pct_com_uti": grp["UTI_MES_TO"].apply(lambda x: (x > 0).mean() * 100),
        "idade_media": grp["IDADE"].mean(),
        "val_medio_aih": grp["VAL_TOT"].mean(),
    }).reset_index()

    # Ordena pela ordem cronológica definida em ONDAS.
    ordem = {nome: i for i, (nome, _, _) in enumerate(ONDAS)}
    out["_ord"] = out["onda"].map(ordem)
    out = out.sort_values("_ord").drop(columns="_ord").reset_index(drop=True)
    out = out.round(2)
    log.info("ondas: %d janelas", len(out))
    return out


def build_perfil_covid_vs_outros(df: pd.DataFrame) -> pd.DataFrame:
    """Perfil clínico comparando COVID com os demais motivos de internação."""
    grp = df.groupby("is_covid")
    out = pd.DataFrame({
        "internacoes": grp.size(),
        "obitos": grp["MORTE"].sum(),
        "taxa_obito": 100 * grp["MORTE"].mean(),
        "dias_perm_medio": grp["DIAS_PERM"].mean(),
        "pct_com_uti": grp["UTI_MES_TO"].apply(lambda x: (x > 0).mean() * 100),
        "idade_media": grp["IDADE"].mean(),
        "val_medio_aih": grp["VAL_TOT"].mean(),
    }).reset_index()
    out["grupo"] = out["is_covid"].map({True: "COVID (B342)", False: "Outros motivos"})
    out = out[[
        "grupo", "internacoes", "obitos", "taxa_obito",
        "dias_perm_medio", "pct_com_uti", "idade_media", "val_medio_aih",
    ]].round(2)
    log.info("perfil_covid_vs_outros: %d grupos", len(out))
    return out


def build_demografia_covid(df: pd.DataFrame) -> pd.DataFrame:
    """Internações e óbitos COVID por sexo e faixa etária."""
    covid = df[df["is_covid"]].copy()
    covid["sexo_label"] = covid["SEXO"].map(MAPA_SEXO).fillna("Não informado")

    grp = covid.groupby(["sexo_label", "faixa_etaria"], observed=True)
    out = pd.DataFrame({
        "internacoes": grp.size(),
        "obitos": grp["MORTE"].sum(),
    }).reset_index()
    out["taxa_obito"] = (100 * out["obitos"] / out["internacoes"]).round(2)
    out = out.rename(columns={"sexo_label": "sexo"})
    out = out.sort_values(["sexo", "faixa_etaria"]).reset_index(drop=True)
    log.info("demografia_covid: %d combinações sexo x faixa", len(out))
    return out


def build_municipios_covid(df: pd.DataFrame, top: int = 20) -> pd.DataFrame:
    """Top municípios de internação (MUNIC_MOV) por volume de casos COVID."""
    covid = df[df["is_covid"]].copy()
    grp = covid.groupby("MUNIC_MOV")
    out = pd.DataFrame({
        "internacoes_covid": grp.size(),
        "obitos_covid": grp["MORTE"].sum(),
        "taxa_obito_covid": 100 * grp["MORTE"].mean(),
    }).reset_index()
    out = out.sort_values("internacoes_covid", ascending=False).head(top)
    out = out.rename(columns={"MUNIC_MOV": "munic_mov_ibge"}).round(2)
    out = out.reset_index(drop=True)
    log.info("municipios_covid: top %d municípios", len(out))
    return out


def save_table(df: pd.DataFrame, nome: str, gold_dir: Path = GOLD_DIR) -> None:
    """Salva uma tabela gold em Parquet e CSV."""
    gold_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = gold_dir / f"{nome}.parquet"
    csv_path = gold_dir / f"{nome}.csv"

    pq.write_table(pa.Table.from_pandas(df), parquet_path, compression="snappy")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    log.info(
        "gold/%s -> %s (%d linhas) + CSV",
        nome, parquet_path.name, len(df),
    )


def build_gold(silver_path: Path = SILVER_FILE, gold_dir: Path = GOLD_DIR) -> dict:
    """Executa o pipeline silver para gold do início ao fim."""
    df = load_silver(silver_path)
    df = add_onda(df)

    tabelas = {
        "serie_mensal": build_serie_mensal(df),
        "ondas": build_ondas(df),
        "perfil_covid_vs_outros": build_perfil_covid_vs_outros(df),
        "demografia_covid": build_demografia_covid(df),
        "municipios_covid": build_municipios_covid(df),
    }

    for nome, tabela in tabelas.items():
        save_table(tabela, nome, gold_dir)

    _log_destaques(tabelas)
    return tabelas


def _log_destaques(tabelas: dict) -> None:
    """Loga os números de maior destaque, úteis para a narrativa da análise."""
    log.info("=== DESTAQUES DA CAMADA GOLD ===")

    ondas = tabelas["ondas"]
    pior = ondas.loc[ondas["taxa_obito_covid"].idxmax()]
    log.info(
        "Onda mais letal: %s (taxa de óbito COVID = %.1f%%, %d internações)",
        pior["onda"], pior["taxa_obito_covid"], int(pior["internacoes_covid"]),
    )

    perfil = tabelas["perfil_covid_vs_outros"].set_index("grupo")
    log.info(
        "Taxa de óbito: COVID %.1f%% vs Outros %.1f%%",
        perfil.loc["COVID (B342)", "taxa_obito"],
        perfil.loc["Outros motivos", "taxa_obito"],
    )
    log.info(
        "Uso de UTI: COVID %.1f%% vs Outros %.1f%%",
        perfil.loc["COVID (B342)", "pct_com_uti"],
        perfil.loc["Outros motivos", "pct_com_uti"],
    )

    serie = tabelas["serie_mensal"]
    pico = serie.loc[serie["internacoes_covid"].idxmax()]
    log.info(
        "Mês de pico COVID: %s (%d internações)",
        pd.Timestamp(pico["ano_mes"]).strftime("%Y-%m"),
        int(pico["internacoes_covid"]),
    )


if __name__ == "__main__":
    build_gold()
