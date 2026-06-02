"""
build_model.py: modelo probabilístico de risco de óbito hospitalar (SUS Analytics).

Ajusta uma regressão logística que estima a probabilidade de óbito de uma
internação a partir de fatores clínicos e demográficos disponíveis na silver.
O objetivo não é prever o futuro, e sim quantificar, de forma probabilística,
quanto cada fator (idade, sexo, COVID, UTI, permanência) pesa no risco de óbito,
aprofundando a análise da pergunta de pesquisa sobre mortalidade.

Saídas (data/gold/):
    modelo_coeficientes.csv   variável, coeficiente, odds ratio, interpretação
    modelo_metricas.csv       AUC, acurácia, tamanhos de treino/teste
    modelo_roc.csv            pontos da curva ROC (fpr, tpr)
Figuras (output/figuras/):
    07_modelo_odds.png        odds ratios por fator
    08_modelo_roc.png         curva ROC com AUC

Uso:
    python src/build_model.py

Pré-requisito:
    data/silver/sihsus_sp.parquet (gerado pelo src/transform_silver.py)
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve, accuracy_score
from sklearn.model_selection import train_test_split

SILVER_FILE = Path("../data/silver/sihsus_sp.parquet")
GOLD_DIR = Path("../data/gold")
FIGURAS_DIR = Path("../output/figuras")

RANDOM_STATE = 42
TEST_SIZE = 0.25

# Fatores do modelo e como o odds ratio de cada um deve ser lido.
# Para variáveis contínuas, escalamos a uma unidade interpretável (ex.: idade
# por década) antes de ajustar, para que o odds ratio tenha leitura direta.
COR_BARRA = "#c0392b"
COR_ROC = "#2980b9"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)
for _ruido in ("kaleido", "choreographer", "logistro"):
    logging.getLogger(_ruido).setLevel(logging.WARNING)


def _idade_em_anos(df: pd.DataFrame) -> pd.Series:
    """Converte IDADE/COD_IDADE em idade em anos (mesma regra da silver)."""
    idade = pd.Series(0.0, index=df.index)
    idade = idade.mask(df["COD_IDADE"] == "4", df["IDADE"].astype("float64"))
    idade = idade.mask(df["COD_IDADE"] == "5", df["IDADE"].astype("float64") + 100)
    return idade


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Monta a matriz de fatores X e o alvo y (óbito) a partir da silver.

    Fatores:
        idade_decadas   idade em anos / 10 (odds ratio por década de vida)
        sexo_masculino  1 = masculino, 0 = feminino
        covid           1 = internação por COVID (CID B342)
        usou_uti        1 = teve ao menos um dia de UTI no mês
        dias_perm       dias de permanência (odds ratio por dia)
    """
    X = pd.DataFrame(index=df.index)
    X["idade_decadas"] = _idade_em_anos(df) / 10.0
    X["sexo_masculino"] = (df["SEXO"] == "1").astype(int)
    X["covid"] = df["is_covid"].astype(int)
    X["usou_uti"] = (df["UTI_MES_TO"] > 0).astype(int)
    X["dias_perm"] = df["DIAS_PERM"].astype("float64")
    y = df["MORTE"].astype(int)
    return X, y


ROTULOS = {
    "idade_decadas": "Idade (por década de vida)",
    "sexo_masculino": "Sexo masculino (vs feminino)",
    "covid": "Internação por COVID (vs outros)",
    "usou_uti": "Uso de UTI (vs sem UTI)",
    "dias_perm": "Permanência (por dia internado)",
}


def fit_model(X: pd.DataFrame, y: pd.Series) -> dict:
    """Ajusta a regressão logística e devolve modelo, métricas e ROC."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y,
    )
    log.info("Treino: %d | Teste: %d | Óbitos no treino: %.1f%%",
             len(X_train), len(X_test), 100 * y_train.mean())

    model = LogisticRegression(max_iter=1000, solver="lbfgs")
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
    fpr, tpr, _ = roc_curve(y_test, proba)
    log.info("AUC = %.3f | Acurácia = %.3f", auc, acc)

    return {
        "model": model, "auc": auc, "acc": acc,
        "fpr": fpr, "tpr": tpr,
        "n_train": len(X_train), "n_test": len(X_test),
        "cols": list(X.columns),
    }


def build_coeficientes(fit: dict) -> pd.DataFrame:
    """Tabela de coeficientes e odds ratios, ordenada por efeito."""
    coefs = fit["model"].coef_[0]
    out = pd.DataFrame({
        "variavel": fit["cols"],
        "rotulo": [ROTULOS[c] for c in fit["cols"]],
        "coeficiente": coefs,
        "odds_ratio": np.exp(coefs),
    })
    out["aumenta_risco"] = out["odds_ratio"] > 1
    out = out.sort_values("odds_ratio", ascending=False).reset_index(drop=True)
    out[["coeficiente", "odds_ratio"]] = out[["coeficiente", "odds_ratio"]].round(3)
    return out


def fig_odds(coef: pd.DataFrame) -> go.Figure:
    sub = coef.sort_values("odds_ratio")
    fig = go.Figure(go.Bar(
        x=sub["odds_ratio"], y=sub["rotulo"], orientation="h",
        marker_color=COR_BARRA,
        text=[f"{v:.2f}x" for v in sub["odds_ratio"]], textposition="outside",
        hovertemplate="Odds ratio: %{x:.2f}<extra>%{y}</extra>",
    ))
    fig.add_vline(x=1, line_dash="dash", line_color="#7f8c8d")
    fig.update_xaxes(title_text="Odds ratio (chance de óbito; 1 = sem efeito)")
    fig.update_layout(
        title=dict(text="<b>Fatores associados ao óbito hospitalar</b><br>"
                        "<span style='font-size:13px;color:#666'>"
                        "Regressão logística; acima de 1 aumenta a chance de óbito</span>",
                   x=0.02, xanchor="left"),
        template="plotly_white",
        font=dict(family="Arial, sans-serif", size=13, color="#2c3e50"),
        margin=dict(l=70, r=60, t=90, b=60),
    )
    return fig


def fig_roc(fit: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fit["fpr"], y=fit["tpr"], mode="lines",
        line=dict(color=COR_ROC, width=3),
        name=f"Modelo (AUC = {fit['auc']:.3f})",
        hovertemplate="FPR %{x:.2f} | TPR %{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines",
        line=dict(color="#7f8c8d", width=2, dash="dash"),
        name="Acaso (AUC = 0,5)",
    ))
    fig.update_xaxes(title_text="Falso positivo (1 - especificidade)")
    fig.update_yaxes(title_text="Verdadeiro positivo (sensibilidade)")
    fig.update_layout(
        title=dict(text="<b>Curva ROC do modelo de óbito</b><br>"
                        f"<span style='font-size:13px;color:#666'>"
                        f"AUC = {fit['auc']:.3f}: capacidade de separar óbito de alta</span>",
                   x=0.02, xanchor="left"),
        template="plotly_white",
        font=dict(family="Arial, sans-serif", size=13, color="#2c3e50"),
        legend=dict(orientation="h", yanchor="bottom", y=0.0, xanchor="right", x=1.0),
        margin=dict(l=70, r=40, t=90, b=60),
    )
    return fig


def build_model(
    silver_path: Path = SILVER_FILE,
    gold_dir: Path = GOLD_DIR,
    figuras_dir: Path = FIGURAS_DIR,
) -> dict:
    gold_dir.mkdir(parents=True, exist_ok=True)
    figuras_dir.mkdir(parents=True, exist_ok=True)

    log.info("Lendo silver: %s", silver_path)
    cols = ["MORTE", "IDADE", "COD_IDADE", "SEXO", "is_covid", "UTI_MES_TO", "DIAS_PERM"]
    df = pd.read_parquet(silver_path, columns=cols)
    log.info("Registros: %d", len(df))

    X, y = build_features(df)
    fit = fit_model(X, y)
    coef = build_coeficientes(fit)

    metricas = pd.DataFrame([{
        "auc": round(fit["auc"], 4),
        "acuracia": round(fit["acc"], 4),
        "n_treino": fit["n_train"],
        "n_teste": fit["n_test"],
        "n_fatores": len(fit["cols"]),
    }])
    roc = pd.DataFrame({"fpr": fit["fpr"], "tpr": fit["tpr"]})

    coef.to_csv(gold_dir / "modelo_coeficientes.csv", index=False, encoding="utf-8")
    metricas.to_csv(gold_dir / "modelo_metricas.csv", index=False, encoding="utf-8")
    roc.to_csv(gold_dir / "modelo_roc.csv", index=False, encoding="utf-8")
    log.info("Tabelas do modelo salvas em %s", gold_dir)

    fig_odds(coef).write_image(str(figuras_dir / "07_modelo_odds.png"),
                               width=1100, height=520, scale=2)
    fig_roc(fit).write_image(str(figuras_dir / "08_modelo_roc.png"),
                             width=900, height=600, scale=2)
    log.info("Figuras do modelo salvas em %s", figuras_dir)

    _log_destaques(coef, fit)
    return {"coeficientes": coef, "metricas": metricas, "roc": roc, "fit": fit}


def _log_destaques(coef: pd.DataFrame, fit: dict) -> None:
    log.info("=== DESTAQUES DO MODELO ===")
    log.info("AUC = %.3f (1,0 = perfeito; 0,5 = acaso)", fit["auc"])
    for _, r in coef.iterrows():
        sentido = "aumenta" if r["odds_ratio"] > 1 else "reduz"
        log.info("%-34s OR = %.2f (%s a chance de óbito)",
                 r["rotulo"], r["odds_ratio"], sentido)


if __name__ == "__main__":
    build_model()
