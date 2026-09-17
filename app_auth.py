"""Local account management with the same analysis page used by app.py."""

import streamlit as st

from src.utils.auth import AuthManager
from src.utils.document_manager import DocumentManager
from src.visualization.dashboard import read_csv, render_dashboard
from src.visualization.theme import (
    ROOT,
    apply_theme,
    icon,
    info_box,
    section,
    success_box,
    user_badge,
)


def show_login(auth):
    # Logo + branding centralizado
    st.markdown(
        f'<div class="login-header">'
        f'<div class="login-logo">{icon("activity")}</div>'
        f'<h1 class="login-title">Med / Risco</h1>'
        f'<p class="login-subtitle">Gestão de abastecimento farmacêutico · IFCE</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    _, center, _ = st.columns([1, 2, 1])
    with center:
        login_tab, register_tab = st.tabs(["Entrar", "Criar conta"])

        with login_tab:
            st.markdown(
                f'<div class="tab-header">{icon("log-in")} <strong>Acesse sua conta</strong></div>',
                unsafe_allow_html=True,
            )
            with st.form("login"):
                username = st.text_input("Usuário", placeholder="nome de usuário")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                    success, user = auth.authenticate(username, password)
                    if success:
                        st.session_state["user"] = user
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")

        with register_tab:
            st.markdown(
                f'<div class="tab-header">{icon("user")} <strong>Crie sua conta</strong></div>',
                unsafe_allow_html=True,
            )
            with st.form("register"):
                name     = st.text_input("Nome completo", placeholder="Seu nome")
                username = st.text_input("Nome de usuário", placeholder="usuario")
                email    = st.text_input("Email", placeholder="email@exemplo.com")
                password = st.text_input("Nova senha", type="password", placeholder="••••••••")
                confirm  = st.text_input("Confirme a senha", type="password", placeholder="••••••••")
                if st.form_submit_button("Criar conta", use_container_width=True):
                    if password != confirm:
                        st.error("As senhas não coincidem.")
                    elif not name.strip():
                        st.error("Informe seu nome.")
                    else:
                        ok, message = auth.register_user(username, password, email, name)
                        if ok:
                            success_box(message)
                        else:
                            st.error(message)


def show_documents(manager, user):
    section(
        "Históricos de consumo",
        "database",
        "Arquivos validados podem ser selecionados como fonte no dashboard.",
    )
    uploaded    = st.file_uploader("Enviar histórico mensal", type=["csv"])
    description = st.text_input(
        "Descrição do arquivo", max_chars=200, placeholder="Ex.: Consumo CAPS — Jan 2025"
    )
    valid = False
    if uploaded:
        try:
            preview = read_csv(uploaded)
            valid, message = manager.validate_medication_csv(preview)
            if valid:
                success_box(message)
            else:
                st.error(message)
            st.dataframe(preview.head(10), use_container_width=True, hide_index=True)
        except (ValueError, UnicodeError) as error:
            st.error(f"Falha ao ler o CSV: {error}")

    if st.button("Salvar documento", disabled=not valid, type="primary"):
        ok, message, _ = manager.save_uploaded_file(uploaded, user["username"], description)
        if ok:
            success_box(message)
            st.rerun()
        else:
            st.error(message)

    st.caption(
        "Colunas obrigatórias: medicamento, data (YYYY-MM), consumo e estoque_atual. "
        "Unidade é opcional. Mantenha dose, apresentação e unidade de medida no nome do medicamento."
    )

    files = (
        manager.get_all_files()
        if user["role"] == "admin"
        else manager.get_user_files(user["username"])
    )
    if not files:
        info_box("Nenhum documento salvo ainda. Envie um arquivo acima.")
        return

    st.markdown(
        f'<div class="doc-count">{icon("file-text")} <span>{len(files)} documento(s) disponível(is)</span></div>',
        unsafe_allow_html=True,
    )

    for item in files:
        with st.expander(item["original_name"]):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(
                    f'<div class="doc-meta">'
                    f'{icon("user")} {item["username"]}&nbsp;&nbsp;'
                    f'{icon("key")} {item["upload_date"][:10]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if item["description"]:
                    st.write(item["description"])
            with col2:
                if st.button("Excluir", key=item["file_id"], type="secondary"):
                    ok, message = manager.delete_file(
                        item["file_id"], user["username"], user["role"] == "admin"
                    )
                    if ok:
                        st.rerun()
                    st.error(message)


def show_profile(auth, user):
    section("Minha conta", "user")

    col1, col2 = st.columns([1, 3])
    with col1:
        initial = (user.get("full_name") or "U")[0].upper()
        st.markdown(
            f'<div style="width:72px;height:72px;background:linear-gradient(135deg,#227767,#3a9b8a);'
            f'border-radius:50%;display:flex;align-items:center;justify-content:center;'
            f'font-size:28px;font-weight:700;color:white;margin:8px 0 16px;">{initial}</div>',
            unsafe_allow_html=True,
        )
    with col2:
        role_label = "Administrador" if user.get("role") == "admin" else "Usuário padrão"
        st.markdown(
            f'<table class="profile-table">'
            f'<tr><td>{icon("user")}</td><td><b>Nome</b></td><td>{user["full_name"]}</td></tr>'
            f'<tr><td>{icon("key")}</td><td><b>Usuário</b></td><td><code>{user["username"]}</code></td></tr>'
            f'<tr><td>{icon("info")}</td><td><b>Email</b></td><td>{user["email"]}</td></tr>'
            f'<tr><td>{icon("shield-check")}</td><td><b>Perfil</b></td><td>{role_label}</td></tr>'
            f'</table>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    section("Alterar senha", "shield-check")
    with st.form("password"):
        old     = st.text_input("Senha atual", type="password")
        new     = st.text_input("Nova senha", type="password")
        confirm = st.text_input("Confirmar nova senha", type="password")
        if st.form_submit_button("Atualizar senha", type="primary"):
            if new != confirm:
                st.error("As senhas não coincidem.")
            else:
                ok, message = auth.change_password(user["username"], old, new)
                if ok:
                    success_box(message)
                else:
                    st.error(message)


def main():
    st.set_page_config(
        page_title="Med / Risco — Sistema de Gestão Farmacêutica",
        page_icon="💊",
        layout="wide",
    )
    apply_theme()
    auth    = AuthManager(str(ROOT / "data" / "users.json"))
    manager = DocumentManager(str(ROOT / "data" / "uploads"))
    user    = st.session_state.get("user")

    if not user:
        show_login(auth)
        return

    with st.sidebar:
        user_badge(user.get("full_name", "Usuário"), user.get("role", ""))
        st.markdown("---")
        menu = st.radio(
            "Navegação",
            ["Dashboard", "Documentos", "Perfil"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        if st.button("Sair", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    if menu == "Documentos":
        show_documents(manager, user)
    elif menu == "Perfil":
        show_profile(auth, user)
    else:
        render_dashboard(manager, user)


if __name__ == "__main__":
    main()
