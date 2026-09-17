"""Local Lucide SVGs and a shared, accessible visual language."""

from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
ICON_NAMES = {
    # originals
    "activity",
    "pill",
    "triangle-alert",
    "shield-check",
    "package",
    "chart-no-axes-combined",
    "database",
    "sliders-horizontal",
    "clipboard-list",
    "arrow-up-right",
    "hospital",
    # new
    "key",
    "trending-up",
    "flask-conical",
    "layout-dashboard",
    "download",
    "folder-open",
    "info",
    "user",
    "log-in",
    "check-circle-2",
    "alert-circle",
    "file-text",
    "bar-chart-3",
    "settings-2",
}


@lru_cache
def icon(name: str) -> str:
    if name not in ICON_NAMES:
        raise ValueError(f"Ícone não cadastrado: {name}")
    svg = (ROOT / "assets" / "lucide" / f"{name}.svg").read_text(encoding="utf-8")
    return " ".join(svg.replace("<svg", '<svg aria-hidden="true" focusable="false"').split())


def section(title: str, symbol: str, subtitle: str = ""):
    st.markdown(
        f'<div class="section-title">{icon(symbol)}<h2>{escape(title)}</h2></div>'
        f'<p class="section-subtitle">{escape(subtitle)}</p>',
        unsafe_allow_html=True,
    )


def apply_theme():
    css = (ROOT / "assets" / "dashboard.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def info_box(message: str):
    """Caixa informativa com ícone Lucide."""
    st.markdown(
        f'<div class="custom-info">{icon("info")}<span>{escape(message)}</span></div>',
        unsafe_allow_html=True,
    )


def warning_box(message: str):
    """Caixa de aviso com ícone Lucide."""
    st.markdown(
        f'<div class="custom-warning">{icon("alert-circle")}<span>{escape(message)}</span></div>',
        unsafe_allow_html=True,
    )


def success_box(message: str):
    """Caixa de sucesso com ícone Lucide."""
    st.markdown(
        f'<div class="custom-success">{icon("check-circle-2")}<span>{escape(message)}</span></div>',
        unsafe_allow_html=True,
    )


def header():
    st.markdown(
        f'<div class="eyebrow">{icon("activity")} MED / RISCO'
        f'<span>GESTÃO DE ABASTECIMENTO · ATENÇÃO BÁSICA</span></div>'
        '<div class="hero">'
        "<div>"
        "<h1>Antecipar a demanda.<br>Planejar o abastecimento.</h1>"
        "<p>Previsões de consumo e prioridades de reposição para a gestão farmacêutica municipal.</p>"
        "</div>"
        '<div class="project-label">'
        "PROTÓTIPO ACADÊMICO"
        "<strong>Crato · Ceará</strong>"
        "IFCE · Não validado operacionalmente"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def user_badge(full_name: str, role: str = ""):
    """Badge de usuário logado na sidebar."""
    initial = (full_name or "U")[0].upper()
    role_label = "Administrador" if role == "admin" else "Usuário"
    st.markdown(
        f'<div class="sidebar-user">'
        f'<div class="sidebar-user-avatar">{escape(initial)}</div>'
        f'<div>'
        f'<div class="sidebar-user-name">{escape(full_name)}</div>'
        f'<div class="sidebar-user-role">{escape(role_label)}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
