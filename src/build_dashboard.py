"""
build_dashboard.py: dashboard interativo do SUS Analytics (camada gold).

Lê as tabelas agregadas da camada gold e monta um dashboard HTML único,
interativo e auto-contido (com o plotly.js embutido, funciona offline).
As funções de figura ficam aqui e são reaproveitadas pelo notebook de
análise (notebooks/03_gold_analise.ipynb), evitando duplicação.

Uso:
    python src/build_dashboard.py

Pré-requisito:
    data/gold/*.parquet (gerados pelo src/build_gold.py)

Saída:
    output/dashboard.html
"""

import logging
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

GOLD_DIR = Path("../data/gold")
OUTPUT_HTML = Path("../output/dashboard.html")
FIGURAS_DIR = Path("../output/figuras")

# Nome de arquivo PNG de cada figura, na mesma ordem de build_figures.
NOMES_FIGURAS = [
    "01_serie_volume",
    "02_serie_mortalidade",
    "03_ondas",
    "04_perfil",
    "05_demografia",
    "06_municipios",
]

# Paleta consistente em todo o dashboard.
COR_COVID = "#c0392b"     # vermelho: COVID
COR_OUTROS = "#2980b9"    # azul: outros motivos
COR_NEUTRA = "#7f8c8d"    # cinza: totais e apoio
CORES_ONDA = ["#e74c3c", "#c0392b", "#922b21", "#7f8c8d"]
COR_MASC = "#2980b9"
COR_FEM = "#c0392b"

# Único código de município que afirmamos pelo nome: 355030 é a capital,
# São Paulo (código IBGE de 6 dígitos usado pelo SIH/SUS). Os demais ficam
# pelo código, para não arriscar uma identificação incorreta.
MUNIC_CAPITAL = "355030"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# O kaleido (export de PNG) e suas dependências logam em nível INFO de forma
# muito verbosa. Silenciamos para manter a saída do pipeline limpa.
for _ruido in ("kaleido", "choreographer", "logistro"):
    logging.getLogger(_ruido).setLevel(logging.WARNING)


def load_gold(gold_dir: Path = GOLD_DIR) -> dict:
    """Carrega todas as tabelas gold em um dicionário de DataFrames."""
    tabelas = {}
    for nome in [
        "serie_mensal", "ondas", "perfil_covid_vs_outros",
        "demografia_covid", "municipios_covid",
    ]:
        tabelas[nome] = pd.read_parquet(gold_dir / f"{nome}.parquet")
    log.info("Tabelas gold carregadas: %s", list(tabelas))
    return tabelas


def _layout(fig: go.Figure, titulo: str, subtitulo: str = "") -> go.Figure:
    """Aplica um layout limpo e consistente a uma figura."""
    titulo_html = f"<b>{titulo}</b>"
    if subtitulo:
        titulo_html += f"<br><span style='font-size:13px;color:#666'>{subtitulo}</span>"
    fig.update_layout(
        title=dict(text=titulo_html, x=0.02, xanchor="left"),
        template="plotly_white",
        font=dict(family="Arial, sans-serif", size=13, color="#2c3e50"),
        margin=dict(l=70, r=40, t=90, b=60),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1.0),
    )
    return fig


def fig_serie_volume(serie: pd.DataFrame) -> go.Figure:
    """Internações mensais: COVID frente a outros motivos. Mostra as ondas."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=serie["ano_mes"], y=serie["internacoes_outros"],
        name="Outros motivos", mode="lines",
        line=dict(color=COR_OUTROS, width=2),
        hovertemplate="%{y:,} internações<extra>Outros</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=serie["ano_mes"], y=serie["internacoes_covid"],
        name="COVID (CID B342)", mode="lines",
        line=dict(color=COR_COVID, width=3), fill="tozeroy",
        fillcolor="rgba(192,57,43,0.12)",
        hovertemplate="%{y:,} internações<extra>COVID</extra>",
    ))
    fig.update_yaxes(title_text="Internações no mês")
    fig.update_xaxes(title_text="Mês")
    return _layout(
        fig,
        "Internações mensais no SUS-SP, 2020–2023",
        "Os picos da curva vermelha marcam as ondas: Gama (mar/2021) e Ômicron (jan/2022)",
    )


def fig_serie_mortalidade(serie: pd.DataFrame) -> go.Figure:
    """Taxa de óbito hospitalar mensal: COVID frente a outros motivos."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=serie["ano_mes"], y=serie["taxa_obito_outros"],
        name="Outros motivos", mode="lines",
        line=dict(color=COR_OUTROS, width=2),
        hovertemplate="%{y:.1f}%<extra>Outros</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=serie["ano_mes"], y=serie["taxa_obito_covid"],
        name="COVID (CID B342)", mode="lines",
        line=dict(color=COR_COVID, width=3),
        hovertemplate="%{y:.1f}%<extra>COVID</extra>",
    ))
    fig.update_yaxes(title_text="Óbitos por 100 internações (%)", ticksuffix="%")
    fig.update_xaxes(title_text="Mês")
    return _layout(
        fig,
        "Taxa de óbito hospitalar por mês",
        "A letalidade da COVID fica muito acima da dos demais motivos em todas as ondas",
    )


def fig_ondas(ondas: pd.DataFrame) -> go.Figure:
    """Comparativo entre ondas: volume, letalidade e uso de UTI das internações COVID."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=ondas["onda"], y=ondas["internacoes_covid"],
        name="Internações COVID", marker_color=COR_NEUTRA, yaxis="y",
        hovertemplate="%{y:,} internações<extra></extra>",
        text=ondas["internacoes_covid"], texttemplate="%{text:,}", textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        x=ondas["onda"], y=ondas["taxa_obito_covid"],
        name="Taxa de óbito (%)", mode="lines+markers+text",
        line=dict(color=COR_COVID, width=3), marker=dict(size=10), yaxis="y2",
        text=[f"{v:.1f}%" for v in ondas["taxa_obito_covid"]], textposition="top center",
        hovertemplate="%{y:.1f}%<extra>Óbito</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=ondas["onda"], y=ondas["pct_com_uti"],
        name="% com UTI", mode="lines+markers",
        line=dict(color="#e67e22", width=3, dash="dot"), marker=dict(size=10), yaxis="y2",
        hovertemplate="%{y:.1f}%<extra>UTI</extra>",
    ))
    fig.update_layout(
        yaxis=dict(title="Internações COVID"),
        yaxis2=dict(title="Percentual (%)", overlaying="y", side="right",
                    ticksuffix="%", range=[0, 40]),
    )
    return _layout(
        fig,
        "Perfil das internações COVID por onda",
        "Gama concentrou o maior volume; a letalidade hospitalar passou de 22% para 24% entre as ondas",
    )


def fig_demografia(demografia: pd.DataFrame) -> go.Figure:
    """Taxa de óbito COVID por faixa etária e sexo."""
    ordem = ["0-4", "5-14", "15-29", "30-44", "45-59", "60-74", "75+"]
    fig = go.Figure()
    for sexo, cor in [("Masculino", COR_MASC), ("Feminino", COR_FEM)]:
        sub = demografia[demografia["sexo"] == sexo].set_index("faixa_etaria").reindex(ordem)
        fig.add_trace(go.Bar(
            x=ordem, y=sub["taxa_obito"], name=sexo, marker_color=cor,
            hovertemplate="%{y:.1f}%<extra>" + sexo + "</extra>",
        ))
    fig.update_yaxes(title_text="Óbitos por 100 internações (%)", ticksuffix="%")
    fig.update_xaxes(title_text="Faixa etária (anos)")
    fig.update_layout(barmode="group")
    return _layout(
        fig,
        "Letalidade da COVID por faixa etária e sexo",
        "A taxa de óbito cresce com a idade e é maior entre homens em quase todas as faixas",
    )


def fig_perfil(perfil: pd.DataFrame) -> go.Figure:
    """Comparativo do perfil clínico COVID vs outros motivos (indicadores)."""
    p = perfil.set_index("grupo")
    metricas = [
        ("Taxa de óbito", "taxa_obito", "%"),
        ("% que usou UTI", "pct_com_uti", "%"),
        ("Dias médios de internação", "dias_perm_medio", ""),
        ("Idade média", "idade_media", ""),
    ]
    fig = go.Figure()
    rotulos = [m[0] for m in metricas]
    fig.add_trace(go.Bar(
        x=rotulos, y=[p.loc["Outros motivos", m[1]] for m in metricas],
        name="Outros motivos", marker_color=COR_OUTROS,
        text=[f"{p.loc['Outros motivos', m[1]]:.1f}{m[2]}" for m in metricas],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        x=rotulos, y=[p.loc["COVID (B342)", m[1]] for m in metricas],
        name="COVID (B342)", marker_color=COR_COVID,
        text=[f"{p.loc['COVID (B342)', m[1]]:.1f}{m[2]}" for m in metricas],
        textposition="outside",
    ))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Valor")
    return _layout(
        fig,
        "COVID frente aos demais motivos de internação",
        "A internação por COVID é mais letal, usa mais UTI, dura mais e atinge pacientes mais velhos",
    )


def fig_municipios(municipios: pd.DataFrame, top: int = 10) -> go.Figure:
    """Top municípios por volume de internações COVID."""
    sub = municipios.head(top).copy()
    sub["rotulo"] = sub["munic_mov_ibge"].apply(
        lambda c: "São Paulo (capital)" if str(c) == MUNIC_CAPITAL else f"IBGE {c}"
    )
    sub = sub.iloc[::-1]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sub["internacoes_covid"], y=sub["rotulo"], orientation="h",
        marker_color=COR_COVID,
        text=sub["internacoes_covid"], texttemplate="%{text:,}", textposition="outside",
        hovertemplate="%{x:,} internações COVID<extra>%{y}</extra>",
    ))
    fig.update_xaxes(title_text="Internações COVID")
    return _layout(
        fig,
        f"Concentração geográfica: top {top} municípios de internação",
        "A capital concentra a maior parte das internações COVID do estado",
    )


def build_figures(tabelas: dict) -> list:
    """Constrói todas as figuras do dashboard, na ordem de apresentação."""
    return [
        fig_serie_volume(tabelas["serie_mensal"]),
        fig_serie_mortalidade(tabelas["serie_mensal"]),
        fig_ondas(tabelas["ondas"]),
        fig_perfil(tabelas["perfil_covid_vs_outros"]),
        fig_demografia(tabelas["demografia_covid"]),
        fig_municipios(tabelas["municipios_covid"]),
    ]


def _kpis(tabelas: dict) -> list:
    """Cartões de número-chave exibidos no topo do dashboard."""
    perfil = tabelas["perfil_covid_vs_outros"].set_index("grupo")
    serie = tabelas["serie_mensal"]
    covid = int(perfil.loc["COVID (B342)", "internacoes"])
    obitos_covid = int(perfil.loc["COVID (B342)", "obitos"])
    pico = serie.loc[serie["internacoes_covid"].idxmax()]
    return [
        ("Internações por COVID", f"{covid:,}".replace(",", ".")),
        ("Óbitos por COVID", f"{obitos_covid:,}".replace(",", ".")),
        ("Letalidade hospitalar COVID", f"{perfil.loc['COVID (B342)', 'taxa_obito']:.1f}%"),
        ("Mês de pico (Gama)",
         f"{pd.Timestamp(pico['ano_mes']).strftime('%m/%Y')}"),
    ]


def build_html(tabelas: dict, output: Path = OUTPUT_HTML) -> Path:
    """Monta o dashboard HTML único e auto-contido."""
    output.parent.mkdir(parents=True, exist_ok=True)
    figuras = build_figures(tabelas)

    # A primeira figura embute o plotly.js inline (fica offline); as demais
    # reaproveitam a mesma biblioteca já carregada na página.
    blocos = []
    for i, fig in enumerate(figuras):
        blocos.append(fig.to_html(
            full_html=False,
            include_plotlyjs="inline" if i == 0 else False,
            config={"displayModeBar": True, "responsive": True},
        ))

    kpi_html = "".join(
        f"<div class='kpi'><div class='kpi-val'>{v}</div>"
        f"<div class='kpi-lbl'>{l}</div></div>"
        for l, v in _kpis(tabelas)
    )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SUS Analytics — Impacto da COVID-19 nas internações (SP, 2020–2023)</title>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; margin: 0; background: #f4f6f8; color: #2c3e50; }}
  header {{ background: #1a2942; color: #fff; padding: 28px 40px; }}
  header h1 {{ margin: 0 0 6px; font-size: 24px; }}
  header p {{ margin: 0; color: #aebfd6; font-size: 14px; }}
  .kpis {{ display: flex; flex-wrap: wrap; gap: 16px; padding: 24px 40px; }}
  .kpi {{ background: #fff; border-radius: 10px; padding: 18px 24px; flex: 1 1 180px;
          box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-left: 4px solid #c0392b; }}
  .kpi-val {{ font-size: 28px; font-weight: 700; color: #1a2942; }}
  .kpi-lbl {{ font-size: 13px; color: #7f8c8d; margin-top: 4px; }}
  .chart {{ background: #fff; border-radius: 10px; margin: 0 40px 24px; padding: 10px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  footer {{ padding: 20px 40px 40px; color: #7f8c8d; font-size: 12px; }}
</style>
</head>
<body>
<header>
  <h1>SUS Analytics — Impacto da COVID-19 nas internações hospitalares</h1>
  <p>São Paulo · 2020 a 2023 · Fonte: SIH/SUS (DATASUS) · Camada gold do pipeline de Big Data</p>
</header>
<div class="kpis">{kpi_html}</div>
{"".join(f'<div class="chart">{b}</div>' for b in blocos)}
<footer>
  Dashboard gerado a partir da camada gold (<code>data/gold/</code>) pelo
  <code>src/build_dashboard.py</code>. Dados públicos do DATASUS, Ministério da Saúde.
  COVID-19 identificada pelo CID <b>B342</b>, como registrado no SIH/SUS.
</footer>
</body>
</html>"""

    output.write_text(html, encoding="utf-8")
    log.info("Dashboard salvo em: %s (%.0f KB)", output, output.stat().st_size / 1024)
    return output


def export_figuras_png(tabelas: dict, figuras_dir: Path = FIGURAS_DIR) -> list:
    """Exporta cada figura como PNG estático.

    O GitHub não renderiza Plotly interativo dentro do repositório, então os
    PNGs são o que aparece embutido no README (relatório) e garantem que as
    visualizações sejam vistas mesmo sem rodar nada.
    """
    figuras_dir.mkdir(parents=True, exist_ok=True)
    figuras = build_figures(tabelas)
    caminhos = []
    for nome, fig in zip(NOMES_FIGURAS, figuras):
        caminho = figuras_dir / f"{nome}.png"
        fig.write_image(str(caminho), width=1100, height=520, scale=2)
        caminhos.append(caminho)
        log.info("figura/%s.png", nome)
    return caminhos


def build_dashboard(
    gold_dir: Path = GOLD_DIR,
    output: Path = OUTPUT_HTML,
    figuras_dir: Path = FIGURAS_DIR,
) -> Path:
    tabelas = load_gold(gold_dir)
    export_figuras_png(tabelas, figuras_dir)
    return build_html(tabelas, output)


if __name__ == "__main__":
    build_dashboard()
