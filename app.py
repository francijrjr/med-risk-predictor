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

st.set_page_config(
    page_title="Predição de Escassez de Medicamentos",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data
def load_and_process_data():
    loader = DataLoader()
    df_raw = loader.load_data(source='auto')
    
    if df_raw.empty:
        st.error("Erro ao carregar dados")
        return None, None
    
    cleaner = DataCleaner()
    df_clean = cleaner.clean(df_raw)
    df_aggregated = cleaner.aggregate_monthly(df_clean)
    
    feature_engineer = FeatureEngineer()
    
    all_features = []
    for medicamento in df_aggregated['medicamento'].unique():
        med_data = df_aggregated[df_aggregated['medicamento'] == medicamento].copy()
        med_features = feature_engineer.create_features(med_data)
        all_features.append(med_features)
    
    df_features = pd.concat(all_features, ignore_index=True)
    df_features = feature_engineer.prepare_for_training(df_features)
    
    return df_aggregated, df_features


@st.cache_resource
def train_model(df_features):
    predictor, metrics = train_medication_model(df_features)
    return predictor, metrics


def main():
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
    selected_med = st.selectbox(
        "Selecione um medicamento:",
        medicamentos,
        index=0
    )
    
    if selected_med:
        dashboard.plot_historical_vs_prediction(df_clean, predictions, selected_med)
    
    st.divider()

    st.subheader("Painel de Alertas por Medicamento")

    risk_order = {'Alto': 1, 'Médio': 2, 'Baixo': 3}
    risk_df['_order'] = risk_df['nivel_risco'].map(risk_order)
    risk_df_sorted = risk_df.sort_values(['_order', 'deficit'], ascending=[True, False])
    risk_df_sorted = risk_df_sorted.drop('_order', axis=1)
    tab1, tab2, tab3 = st.tabs(["Visão Geral", "🔴 Alto Risco", "🟡 Médio Risco"])
    
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

    with st.expander("Informações Técnicas"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Dados**")
            st.write(f"- Total de registros: {len(df_clean)}")
            st.write(f"- Medicamentos: {df_clean['medicamento'].nunique()}")
            st.write(f"- Período: {df_clean['data'].min()} a {df_clean['data'].max()}")
            
            st.markdown("**Modelo**")
            st.write(f"- Algoritmo: Random Forest Regressor")
            st.write(f"- Features: {len(predictor.feature_names)}")
            st.write(f"- Horizon: {filters.get('months_prediction', 3)} meses")
        
        with col2:
            st.markdown("**Classificação de Risco**")
            st.write(f"- 🔴 Alto: Estoque < Previsão")
            st.write(f"- 🟡 Médio: Previsão ≤ Estoque < 1.2 × Previsão")
            st.write(f"- 🟢 Baixo: Estoque ≥ 1.2 × Previsão")
            
            st.markdown("**Estatísticas**")
            st.write(f"- Déficit total: {risk_report.get('deficit_total', 0):.0f} unidades")
            st.write(f"- Medicamentos em risco: {risk_stats['Alto'] + risk_stats['Médio']}")
    
    dashboard.show_footer()

    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        download_df = risk_df_sorted[['medicamento', 'estoque_atual', 'consumo_previsto', 
                                      'deficit', 'nivel_risco', 'razao_estoque']].copy()
        
        csv = download_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Baixar Relatório (CSV)",
            data=csv,
            file_name="relatorio_risco_medicamentos.csv",
            mime="text/csv",
            use_container_width=True
        )


if __name__ == "__main__":
    main()
