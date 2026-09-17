"""Standalone entry point. The authenticated version shares the same dashboard."""

import streamlit as st

from src.visualization.dashboard import render_dashboard
from src.visualization.theme import apply_theme


def main():
    st.set_page_config(
        page_title="Med / Risco — Gestão de Abastecimento Farmacêutico",
        page_icon="💊",
        layout="wide",
    )
    apply_theme()
    render_dashboard()


if __name__ == "__main__":
    main()
