"""Shared dashboard: explicit provenance, TCC risk rules and temporal evaluation."""

from html import escape

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analysis import analyze
from src.models.risk_classifier import RISK_COLORS
from src.utils.helpers import format_number
from src.visualization.theme import (
    ROOT,
    header,
    icon,
    info_box,
    section,
    user_badge,
    warning_box,
)


@st.cache_data(show_spinner=False, max_entries=8)
def cached_analysis(raw, months, safety):
    return analyze(raw, months, safety)


def read_csv(source):
    """Accept Brazilian spreadsheets exported with either commas or semicolons."""
    return pd.read_csv(source, sep=None, engine="python")


def chart_style(fig, height=340):
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#1e3d38", size=12),
        margin=dict(l=10, r=20, t=20, b=20),
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=12)),
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(size=11))
    fig.update_yaxes(gridcolor="#e1e8e1", tickfont=dict(size=11))
    return fig


def show_kpis(risks):
    counts = risks["nivel_risco"].value_counts()
    cards = [
        (
            "Séries analisadas",
            len(risks),
            "Uma série por unidade e medicamento",
            "pill",
            "",
        ),
        (
            "Prioridade alta",
            counts.get("Alto", 0),
            "Índice de risco acima de 1,3",
            "triangle-alert",
            "critical",
        ),
        (
            "Em atenção",
            counts.get("Médio", 0),
            "Índice entre 1,0 e 1,3",
            "shield-check",
            "warning",
        ),
        (
            "Dados pendentes",
            counts.get("Sem dados", 0),
            "Séries sem classificação no recorte",
            "database",
            "muted",
        ),
    ]
    content = "".join(
        f'<div class="kpi {style}">'
        f'<div class="kpi-top">{label}{icon(symbol)}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-note">{note}</div>'
        f'</div>'
        for label, value, note, symbol, style in cards
    )
    st.markdown(f'<div class="kpi-grid">{content}</div>', unsafe_allow_html=True)


def show_alerts(risks):
    high = (
        risks[risks["nivel_risco"].eq("Alto")].sort_values("indice_risco", ascending=False).head(3)
    )
    if high.empty:
        st.markdown(
            f'<div class="custom-success">{icon("check-circle-2")}'
            f'<span>Nenhum alerta de risco alto no recorte selecionado.</span></div>',
            unsafe_allow_html=True,
        )
        return
    for column, (_, row) in zip(st.columns(len(high)), high.iterrows()):
        with column:
            st.markdown(
                f'<div class="alert-card">'
                f'<div class="alert-label">{icon("triangle-alert")} PRIORIDADE ALTA</div>'
                f'<h3>{escape(row["medicamento"])}</h3>'
                f'<p>{escape(row["unidade"])}</p>'
                f'<p>Saldo de {escape(row["data_estoque"])}: <strong>{format_number(row["estoque_atual"], 0)}</strong></p>'
                f'<p>Reposição estimada: <strong>{format_number(np.ceil(row["deficit"]), 0)}</strong></p>'
                f'<p>Avaliar compra ou redistribuição.</p>'
                f'</div>',
                unsafe_allow_html=True,
            )


def show_risk_table(risks):
    columns = {
        "unidade": "Unidade",
        "medicamento": "Medicamento",
        "data_estoque": "Mês do saldo",
        "estoque_atual": "Saldo disponível",
        "consumo_previsto": "Demanda prevista",
        "estoque_seguranca": "Reserva de segurança",
        "necessidade_total": "Necessidade total",
        "indice_risco": "Índice de risco",
        "deficit": "Reposição estimada",
        "nivel_risco": "Risco",
        "acao_sugerida": "Ação sugerida",
    }
    table = risks[list(columns)].rename(columns=columns)
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            label: st.column_config.NumberColumn(label, format="%.1f")
            for key, label in columns.items()
            if key
            in (
                "estoque_atual",
                "consumo_previsto",
                "estoque_seguranca",
                "necessidade_total",
                "indice_risco",
                "deficit",
            )
        },
    )
    st.caption(
        "Quantidades na unidade de cada medicamento. Valores de apresentações diferentes não são somados. Reposição inclui a reserva de segurança."
    )


def select_series(frame, unit, medicine):
    return frame[frame["unidade"].eq(unit) & frame["medicamento"].eq(medicine)]


def show_forecast(result, risks):
    choices = list(zip(risks["unidade"], risks["medicamento"]))
    if not choices:
        info_box("Selecione ao menos um nível de risco para explorar as previsões.")
        return
    labels = [f"{index + 1}. {unit} / {medicine}" for index, (unit, medicine) in enumerate(choices)]
    selected = st.selectbox("Unidade / medicamento", labels)
    unit, medicine = choices[labels.index(selected)]
    history = select_series(result.history, unit, medicine)
    prediction = select_series(result.predictions, unit, medicine)
    window = st.select_slider("Histórico exibido (meses)", options=[6, 12, 18, 24, 36], value=12)
    history = history.tail(window)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history["data"],
            y=history["consumo"],
            name="Consumo observado",
            line=dict(color="#227767", width=2.5),
            mode="lines+markers",
            marker=dict(size=6, color="#227767"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=prediction["data"],
            y=prediction["consumo_previsto"],
            name="Previsão",
            line=dict(color="#b57825", width=2.5, dash="dash"),
            mode="lines+markers",
            marker=dict(size=6, color="#b57825", symbol="diamond"),
        )
    )
    fig.update_layout(hovermode="x unified", yaxis_title="Quantidade na unidade do medicamento")
    st.plotly_chart(chart_style(fig, 380), use_container_width=True)
    row = select_series(risks, unit, medicine).iloc[0]
    for col, key, label in zip(
        st.columns(4),
        ["estoque_atual", "consumo_previsto", "estoque_seguranca", "necessidade_total"],
        [
            "Saldo disponível",
            "Demanda no horizonte",
            "Reserva de segurança",
            "Necessidade total",
        ],
    ):
        col.metric(label, "Não informado" if pd.isna(row[key]) else format_number(row[key], 1))
    st.caption(
        f"Saldo referente a {row['data_estoque']}. Previsões pontuais; intervalos de incerteza ainda não estimados."
    )


def show_method(result, months, safety, source):
    section("Como interpretar os resultados", "clipboard-list")
    st.write(
        f"Reserva de segurança: **{safety:.0%}** da demanda prevista nos próximos **{months} meses após o último registro de cada série**."
    )
    st.code(
        "Necessidade total = demanda prevista + reserva de segurança\nÍndice de risco = necessidade total / saldo disponível",
        language=None,
    )
    st.write("**Baixo:** índice < 1,0 · **Médio:** 1,0 ≤ índice ≤ 1,3 · **Alto:** índice > 1,3.")
    st.caption(
        "Saldo zero com demanda positiva gera risco alto. Saldo desconhecido ou saldo e demanda ambos zero geram 'Sem dados'. Limiares ilustrativos do TCC, ainda sem calibração municipal."
    )
    section(
        "Avaliação temporal",
        "bar-chart-3",
        "Comparação retrospectiva por unidade e medicamento; R² não é acurácia.",
    )
    st.write(
        f"Os últimos {months} meses de cada série são reservados para teste. O modelo prevê todo esse intervalo sem acessar seus consumos reais. A referência simples repete o último consumo conhecido. Depois da avaliação, o modelo é treinado novamente com todo o histórico."
    )
    evaluation = result.metrics.copy()
    evaluation["supera_baseline"] = np.where(
        evaluation["mae"] < evaluation["mae_baseline"], "Sim", "Não"
    )
    st.dataframe(
        evaluation.rename(
            columns={
                "unidade": "Unidade",
                "medicamento": "Medicamento",
                "mae": "MAE",
                "rmse": "RMSE",
                "r2": "R²",
                "mae_baseline": "MAE da referência",
                "supera_baseline": "Supera referência",
                "treino_ate": "Treino até",
                "teste_de": "Teste de",
                "teste_ate": "Teste até",
                "meses_teste": "Meses em teste",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "MAE e RMSE menores indicam erros menores. R² fica indisponível para teste de um mês ou consumo constante. Uma única janela de teste não comprova generalização operacional."
    )
    section("Origem e limitações", "file-text")
    st.write(
        f"**Base:** {source}. **Período:** {result.history['data'].min()} a {result.history['data'].max()}. **Registros:** {len(result.history)}."
    )
    st.write(
        "A integração automática ao DATASUS não está ativa. O modelo utiliza consumo passado e calendário; indicadores epidemiológicos, prazo de entrega, validade e entradas futuras ainda não participam do cálculo."
    )
    st.write(
        "O saldo informado é comparado à demanda acumulada do horizonte, sem reposições intermediárias. As sugestões apoiam a análise do gestor e não executam compras."
    )
    st.dataframe(result.history, use_container_width=True, hide_index=True)


def render_dashboard(doc_manager=None, user=None):
    header()
    with st.sidebar:
        # --- User badge (quando autenticado) ---
        if user:
            user_badge(user.get("full_name", "Usuário"), user.get("role", ""))
            st.markdown("---")

        section("Configurar análise", "settings-2")
        modes = ["Demonstração", "Enviar CSV"]
        files = []
        if doc_manager and user:
            files = (
                doc_manager.get_all_files()
                if user.get("role") == "admin"
                else doc_manager.get_user_files(user["username"])
            )
            if files:
                modes.append("Documentos salvos")
        mode = st.radio("Fonte dos dados", modes)
        raw = None
        source = "Arquivo de exemplo local — procedência não validada"
        try:
            if mode == "Demonstração":
                raw = read_csv(ROOT / "data" / "samples" / "datasus_sample.csv")
            elif mode == "Enviar CSV":
                uploaded = st.file_uploader("Histórico mensal (.csv)", type=["csv"])
                st.caption(
                    "Obrigatórias: medicamento, data, consumo, estoque_atual. Opcional: unidade."
                )
                if uploaded:
                    raw = read_csv(uploaded)
                    source = f"Arquivo enviado: {uploaded.name} — origem declarada pelo usuário"
            else:
                file_ids = {item["file_id"]: item for item in files}
                chosen = st.selectbox(
                    "Documento",
                    list(file_ids),
                    format_func=lambda key: file_ids[key]["original_name"],
                )
                raw = doc_manager.load_csv_to_dataframe(chosen)
                source = f"Documento salvo: {file_ids[chosen]['original_name']} — origem declarada pelo usuário"
        except (ValueError, OSError, UnicodeError) as error:
            st.error(f"Não foi possível ler o CSV: {error}")
        months = st.slider("Horizonte de previsão (meses)", 1, 6, 3)
        safety = st.slider("Reserva de segurança (%)", 0, 100, 20, 5) / 100
        st.caption("Percentual para simulação. Ajuste com o gestor antes de uso operacional.")

    if raw is None:
        info_box("Selecione uma fonte de dados na barra lateral para iniciar a análise.")
        return

    # Source note com ícone Lucide file-text
    st.markdown(
        f'<div class="source-note">{icon("file-text")}<span>{escape(source)}</span></div>',
        unsafe_allow_html=True,
    )

    try:
        with st.spinner("Preparando séries, avaliando previsões e calculando riscos…"):
            result = cached_analysis(raw, months, safety)
    except ValueError as error:
        st.error(str(error))
        return

    if result.skipped:
        warning_box(
            f"{len(result.skipped)} série(s) sem histórico suficiente foram excluídas da previsão."
        )
        with st.expander("Ver séries não analisadas"):
            st.write("\n\n".join(result.skipped))

    latest = pd.Period(result.history["data"].max(), freq="M")
    if latest < pd.Period(pd.Timestamp.today(), freq="M") - 1:
        warning_box(
            f"O histórico termina em {latest}. Os alertas representam esse período, não o estoque de hoje."
        )

    with st.sidebar:
        st.markdown("---")
        units = st.multiselect(
            "Unidades",
            sorted(result.risks["unidade"].unique()),
            default=sorted(result.risks["unidade"].unique()),
        )
        levels = st.multiselect("Níveis de risco", list(RISK_COLORS), default=list(RISK_COLORS))

    risks = result.risks[
        result.risks["unidade"].isin(units) & result.risks["nivel_risco"].isin(levels)
    ]

    show_kpis(risks)

    overview, forecasts, method = st.tabs(["Visão geral", "Demanda e estoque", "Método e dados"])

    with overview:
        section(
            "Prioridades de abastecimento",
            "triangle-alert",
            f"Demanda acumulada de {months} mês(es) após o último registro · reserva de {safety:.0%}",
        )
        show_alerts(risks)

        left, right = st.columns([1, 2])
        with left:
            section("Situação do estoque", "shield-check")
            counts = risks["nivel_risco"].value_counts()
            if counts.empty:
                info_box("Nenhuma série nos filtros selecionados.")
            else:
                fig = go.Figure(
                    go.Pie(
                        labels=counts.index,
                        values=counts.values,
                        hole=0.72,
                        marker_colors=[RISK_COLORS[level] for level in counts.index],
                        textinfo="value",
                        sort=False,
                        textfont=dict(size=14, family="Inter, sans-serif"),
                    )
                )
                fig.update_layout(
                    annotations=[
                        dict(
                            text=f"<b>{len(risks)}</b><br><span style='font-size:12px'>séries</span>",
                            x=0.5,
                            y=0.5,
                            showarrow=False,
                            font=dict(size=20, family="Inter, sans-serif", color="#0f2b27"),
                        )
                    ]
                )
                st.plotly_chart(chart_style(fig), use_container_width=True)

        with right:
            section(
                "Prioridade pelo índice de risco",
                "trending-up",
                "Necessidade total em relação ao saldo; permite comparar apresentações diferentes.",
            )
            ranking = (
                risks[np.isfinite(risks["indice_risco"])]
                .nlargest(8, "indice_risco")
                .sort_values("indice_risco")
            )
            if not ranking.empty:
                fig = go.Figure(
                    go.Bar(
                        x=ranking["indice_risco"],
                        y=ranking["medicamento"] + " / " + ranking["unidade"],
                        orientation="h",
                        marker_color=[RISK_COLORS[level] for level in ranking["nivel_risco"]],
                        marker_line_width=0,
                        text=ranking["indice_risco"].round(2),
                        textposition="outside",
                        textfont=dict(size=11, family="Inter, sans-serif"),
                    )
                )
                fig.add_vline(x=1.3, line_dash="dot", line_color="#b03028", line_width=1.5)
                st.plotly_chart(chart_style(fig), use_container_width=True)
            st.caption(
                "Saldos zero e desconhecidos são exibidos na tabela, fora da escala do gráfico."
            )

        section("Plano de acompanhamento", "package")
        show_risk_table(risks)
        export = risks.assign(
            fonte=source, horizonte_meses=months, percentual_seguranca=safety * 100
        )
        # Botão de download com ícone Lucide inline
        st.markdown(
            f'<div class="download-label">{icon("download")} Exportar análise em CSV</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "Baixar CSV",
            export.to_csv(index=False).encode("utf-8-sig"),
            file_name="analise_abastecimento.csv",
            mime="text/csv",
        )

    with forecasts:
        section("Consumo observado e previsão", "trending-up")
        show_forecast(result, risks)

    with method:
        show_method(result, months, safety, source)

    st.markdown(
        f'<div class="footer">'
        f'<span>{icon("activity")} <strong>MED / RISCO</strong> · Protótipo Acadêmico · IFCE</span>'
        f'<span>{icon("hospital")} Gestão de abastecimento farmacêutico · Crato · Ceará</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
