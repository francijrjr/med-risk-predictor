import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.ingestion.loader import DataLoader
from src.preprocessing.cleaning import DataCleaner
from src.features.engineering import FeatureEngineer
from src.models.train import MedicationPredictor, train_medication_model
from src.models.predict import ConsumptionPredictor, make_predictions
from src.models.risk_classifier import RiskClassifier, classify_medication_risk
from src.visualization.dashboard import Dashboard
from src.utils.auth import AuthManager
from src.utils.document_manager import DocumentManager


st.set_page_config(
    page_title="Sistema Preditivo de Medicamentos",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

auth_manager = AuthManager()
doc_manager = DocumentManager()

auth_manager.create_admin_user()


def show_login_page():
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h1> Sistema Preditivo de Escassez de Medicamentos</h1>
        <p style="font-size: 18px; color: #666;">Predição de Consumo em Postos de Saúde da Família</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs([" Login", "Registrar"])
        
        with tab1:
            st.subheader("Acesse sua conta")
            
            username = st.text_input("Usuário", key="login_user")
            password = st.text_input("Senha", type="password", key="login_pass")
            
            if st.button("Entrar", use_container_width=True, type="primary"):
                if username and password:
                    success, user_data = auth_manager.authenticate(username, password)
                    
                    if success:
                        st.session_state['authenticated'] = True
                        st.session_state['user'] = user_data
                        st.success(f"Bem-vindo, {user_data['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos")
                else:
                    st.warning("Preencha todos os campos")
            
            st.info("**Usuário demo:** admin / admin123")
        
        with tab2:
            st.subheader("Criar nova conta")
            
            new_username = st.text_input("Nome de usuário", key="reg_user")
            new_email = st.text_input("Email", key="reg_email")
            new_fullname = st.text_input("Nome completo", key="reg_name")
            new_password = st.text_input("Senha", type="password", key="reg_pass")
            new_password_confirm = st.text_input("Confirmar senha", type="password", key="reg_pass_confirm")
            
            if st.button("Registrar", use_container_width=True, type="primary"):
                if new_password != new_password_confirm:
                    st.error("As senhas não coincidem")
                elif all([new_username, new_email, new_fullname, new_password]):
                    success, message = auth_manager.register_user(
                        new_username,
                        new_password,
                        new_email,
                        new_fullname
                    )
                    
                    if success:
                        st.success(message)
                        st.info("Agora você pode fazer login!")
                    else:
                        st.error(message)
                else:
                    st.warning("Preencha todos os campos")


def show_sidebar():
    user = st.session_state.get('user', {})
    
    st.sidebar.markdown(f"""
    **Nome:** {user.get('full_name', 'N/A')}  
    **Usuário:** {user.get('username', 'N/A')}  
    **Perfil:** {user.get('role', 'user').upper()}
    """)
    
    st.sidebar.divider()
    
    if st.sidebar.button("Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()


def show_upload_page():
    st.title("Gerenciar Documentos")
    
    st.markdown("""
    Envie arquivos CSV com dados de medicamentos para análise.  
    **Formato esperado:** medicamento, data (YYYY-MM), consumo, estoque_atual
    """)
    
    st.divider()

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Enviar Novo Documento")
        
        uploaded_file = st.file_uploader(
            "Selecione um arquivo CSV",
            type=['csv'],
            help="Arquivo CSV com dados de medicamentos"
        )
        
        description = st.text_area("Descrição (opcional)", max_chars=200)
        
        if uploaded_file is not None:
            try:
                df_preview = pd.read_csv(uploaded_file)
                st.info(f"Preview: {len(df_preview)} linhas, {len(df_preview.columns)} colunas")
                st.dataframe(df_preview.head(10), use_container_width=True)
                valid, msg = doc_manager.validate_medication_csv(df_preview)
                if valid:
                    st.success(f"Sucesso {msg}")
                else:
                    st.error(f"Error {msg}")
                
                uploaded_file.seek(0)
                
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {e}")
        
        if st.button("Enviar Arquivo", type="primary", disabled=uploaded_file is None):
            if uploaded_file:
                success, message, file_id = doc_manager.save_uploaded_file(
                    uploaded_file,
                    st.session_state['user']['username'],
                    description
                )
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    with col2:
        st.subheader("ℹInformações")
        st.markdown("""
        **Colunas obrigatórias:**
        - `medicamento`
        - `data` (YYYY-MM)
        - `consumo`
        - `estoque_atual`
        
        **Exemplo:**
        ```
        PARACETAMOL 500MG,2024-01,3245,4200
        IBUPROFENO 600MG,2024-01,2156,2800
        ```
        """)
    
    st.divider()
    
    st.subheader(" Meus Documentos")
    
    user = st.session_state['user']
    is_admin = user.get('role') == 'admin'
    
    if is_admin:
        files = doc_manager.get_all_files()
        st.info(" Modo Admin: Visualizando todos os arquivos")
    else:
        files = doc_manager.get_user_files(user['username'])
    
    if files:
        for file_info in files:
            with st.expander(f" {file_info['original_name']} - {file_info['upload_date'][:10]}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Usuário:** {file_info['username']}")
                    st.write(f"**Data:** {file_info['upload_date']}")
                    st.write(f"**Tamanho:** {file_info['size_bytes']:,} bytes".replace(',', '.'))
                    if file_info['description']:
                        st.write(f"**Descrição:** {file_info['description']}")
                
                with col2:
                    if st.button("Excluir", key=f"del_{file_info['file_id']}"):
                        success, msg = doc_manager.delete_file(
                            file_info['file_id'],
                            user['username'],
                            is_admin
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
    else:
        st.info("Nenhum documento enviado ainda")


def main():
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        show_login_page()
        return

    show_sidebar()

    menu = st.sidebar.radio(
        "Menu",
        [" Dashboard", " Documentos", " Perfil"]
    )
    
    if menu == " Documentos":
        show_upload_page()
    
    elif menu == "Perfil":
        st.title("Meu Perfil")
        user = st.session_state['user']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Informações")
            st.write(f"**Nome:** {user['full_name']}")
            st.write(f"**Usuário:** {user['username']}")
            st.write(f"**Email:** {user['email']}")
            st.write(f"**Perfil:** {user['role'].upper()}")
            st.write(f"**Cadastro:** {user.get('created_at', 'N/A')[:10]}")
        
        with col2:
            st.subheader("Alterar Senha")
            
            old_pass = st.text_input("Senha atual", type="password")
            new_pass = st.text_input("Nova senha", type="password")
            confirm_pass = st.text_input("Confirmar nova senha", type="password")
            
            if st.button("Alterar Senha"):
                if new_pass != confirm_pass:
                    st.error("As senhas não coincidem")
                elif all([old_pass, new_pass]):
                    success, msg = auth_manager.change_password(
                        user['username'],
                        old_pass,
                        new_pass
                    )
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
    
    else:
        from app import load_and_process_data, train_model
        
        dashboard = Dashboard()
        dashboard.show_header()
        
        filters = dashboard.show_filters()
        
        with st.spinner("Carregando e processando dados..."):
            df_clean, df_features = load_and_process_data()
        
        if df_clean is None or df_features is None:
            st.error("Não foi possível carregar os dados")
            return
        
        with st.spinner("Treinando modelo preditivo..."):
            predictor, metrics = train_model(df_features)
        
        with st.spinner("Gerando predições..."):
            feature_engineer = FeatureEngineer()
            consumption_predictor = ConsumptionPredictor(predictor, feature_engineer)
            
            predictions = consumption_predictor.predict_all_medications(
                df_features,
                n_months=filters.get('months_prediction', 3)
            )
        
        with st.spinner("Classificando riscos..."):
            last_stock = df_clean.sort_values('data').groupby('medicamento').last().reset_index()
            last_stock = last_stock[['medicamento', 'estoque_atual']]
            
            pred_summary = predictions.groupby('medicamento')['consumo_previsto'].sum().reset_index()
            pred_summary.columns = ['medicamento', 'consumo_previsto']
            
            risk_data = pred_summary.merge(last_stock, on='medicamento', how='left')
            risk_data['estoque_atual'] = risk_data['estoque_atual'].fillna(0)
            
            classifier = RiskClassifier()
            risk_df = classifier.classify_batch(risk_data)
            
            if filters.get('risk_filter'):
                risk_df = risk_df[risk_df['nivel_risco'].isin(filters['risk_filter'])]
            
            risk_stats = classifier.get_risk_statistics(risk_data)
            risk_report = classifier.create_risk_report(risk_data)
        
        kpi_metrics = {
            'total_medicamentos': len(risk_data),
            'risco_alto': risk_stats.get('Alto', 0),
            'risco_medio': risk_stats.get('Médio', 0),
            'percentual_alto': risk_report.get('percentual_alto', 0),
            'percentual_medio': risk_report.get('percentual_medio', 0),
            'model_r2': metrics.get('test_r2', 0),
            'deficit_total': risk_report.get('deficit_total', 0)
        }
        
        dashboard.show_kpis(kpi_metrics)
        
        high_risk_meds = classifier.get_high_risk_medications(risk_data)
        if not high_risk_meds.empty:
            st.markdown("### Alertas Críticos - Ação Imediata Necessária")
            dashboard.show_critical_alerts(high_risk_meds.head(5))
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribuição de Níveis de Risco")
            dashboard.plot_risk_distribution(risk_stats)
        
        with col2:
            st.subheader("Ranking de Déficit")
            dashboard.plot_deficit_ranking(risk_data, top_n=8)
        
        st.divider()
        
        st.subheader("Análise Histórica vs Predição")
        
        medicamentos = sorted(df_clean['medicamento'].unique())
        selected_med = st.selectbox("Selecione um medicamento:", medicamentos, index=0)
        
        if selected_med:
            dashboard.plot_historical_vs_prediction(df_clean, predictions, selected_med)
        
        st.divider()
        
        st.subheader("Painel de Alertas por Medicamento")
        
        risk_order = {'Alto': 1, 'Médio': 2, 'Baixo': 3}
        risk_df['_order'] = risk_df['nivel_risco'].map(risk_order)
        risk_df_sorted = risk_df.sort_values(['_order', 'deficit'], ascending=[True, False])
        risk_df_sorted = risk_df_sorted.drop('_order', axis=1)
        
        tab1, tab2, tab3 = st.tabs([" Visão Geral", " Alto Risco", "Médio Risco"])
        
        with tab1:
            dashboard.show_enhanced_risk_table(risk_df_sorted)
        
        with tab2:
            alto_risco = risk_df_sorted[risk_df_sorted['nivel_risco'] == 'Alto']
            if not alto_risco.empty:
                dashboard.show_enhanced_risk_table(alto_risco)
                st.markdown(f"**Total: {len(alto_risco)} medicamento(s) em alto risco**")
            else:
                st.success("Nenhum medicamento em alto risco!")
        
        with tab3:
            medio_risco = risk_df_sorted[risk_df_sorted['nivel_risco'] == 'Médio']
            if not medio_risco.empty:
                dashboard.show_enhanced_risk_table(medio_risco)
                st.markdown(f"**Total: {len(medio_risco)} medicamento(s) em médio risco**")
            else:
                st.info("Nenhum medicamento em médio risco")
        
        st.divider()
        
        st.subheader("Performance do Modelo Preditivo")
        dashboard.plot_model_metrics(metrics)
        
        dashboard.show_footer()


if __name__ == "__main__":
    main()
