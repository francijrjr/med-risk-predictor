import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.helpers import get_risk_color, format_number

class Dashboard:

    def __init__(self):
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#00CC66',
            'warning': '#FFA500',
            'danger': '#FF4B4B'
        }
    
    def show_kpis(self, metrics: Dict):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Total de Medicamentos",
                value=metrics.get('total_medicamentos', 0)
            )
        
        with col2:
            alto = metrics.get('risco_alto', 0)
            st.metric(
                label="🔴 Alertas Alto Risco",
                value=alto,
                delta=f"{metrics.get('percentual_alto', 0)}%" if alto > 0 else None,
                delta_color="inverse"
            )
        
        with col3:
            medio = metrics.get('risco_medio', 0)
            st.metric(
                label="🟡 Alertas Médio Risco",
                value=medio,
                delta=f"{metrics.get('percentual_medio', 0)}%" if medio > 0 else None,
                delta_color="inverse"
            )
        
        with col4:
            deficit = metrics.get('deficit_total', 0)
            st.metric(
                label="Déficit Total",
                value=f"{deficit:,.0f}".replace(',', '.'),
                help="Quantidade total de unidades em falta"
            )
        
        with col5:
            r2 = metrics.get('model_r2', 0)
            st.metric(
                label="Acurácia Modelo (R²)",
                value=f"{r2:.1%}" if r2 > 0 else "N/A"
            )
    
    def show_critical_alerts(self, high_risk_df: pd.DataFrame):
        if high_risk_df.empty:
            return
        cols = st.columns(min(len(high_risk_df), 5))
        
        for idx, (_, row) in enumerate(high_risk_df.iterrows()):
            if idx >= 5: 
                break
            
            with cols[idx]:
                medicamento = row['medicamento']
                estoque = row.get('estoque_atual', 0)
                previsao = row.get('consumo_previsto', 0)
                deficit = row.get('deficit', 0)

                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #ff4b4b 0%, #ff6b6b 100%);
                    padding: 15px;
                    border-radius: 10px;
                    border-left: 5px solid #cc0000;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    color: white;
                    margin-bottom: 10px;
                ">
                    <h4 style="margin: 0; font-size: 14px; color: white;"> {medicamento}</h4>
                    <hr style="margin: 8px 0; border-color: rgba(255,255,255,0.3);">
                    <p style="margin: 3px 0; font-size: 12px;"><b>Estoque:</b> {estoque:,.0f}</p>
                    <p style="margin: 3px 0; font-size: 12px;"><b>Previsão:</b> {previsao:,.0f}</p>
                    <p style="margin: 3px 0; font-size: 12px;"><b>Déficit:</b> 🔻 {deficit:,.0f}</p>
                </div>
                """.replace(',', '.'), unsafe_allow_html=True)
    
    def plot_historical_vs_prediction(self, historical: pd.DataFrame, predictions: pd.DataFrame, medicamento: str):
        hist_med = historical[historical['medicamento'] == medicamento].copy()
        pred_med = predictions[predictions['medicamento'] == medicamento].copy()
        
        if hist_med.empty:
            st.warning(f"Sem dados históricos para {medicamento}")
            return

        hist_med = hist_med.sort_values('data')
        pred_med = pred_med.sort_values('data')
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist_med['data'],
            y=hist_med['consumo'],
            mode='lines+markers',
            name='Histórico',
            line=dict(color=self.colors['primary'], width=2),
            marker=dict(size=6)
        ))

        if not pred_med.empty:
            fig.add_trace(go.Scatter(
                x=pred_med['data'],
                y=pred_med['consumo_previsto'],
                mode='lines+markers',
                name='Predição',
                line=dict(color=self.colors['secondary'], width=2, dash='dash'),
                marker=dict(size=8, symbol='diamond')
            ))

        fig.update_layout(
            title=f'Consumo Histórico vs Predição - {medicamento}',
            xaxis_title='Mês',
            yaxis_title='Consumo (unidades)',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def plot_risk_distribution(self, risk_stats: Dict):
        labels = ['🔴 Alto', '🟡 Médio', '🟢 Baixo']
        values = [
            risk_stats.get('Alto', 0),
            risk_stats.get('Médio', 0),
            risk_stats.get('Baixo', 0)
        ]
        colors = ['#FF4B4B', '#FFA500', '#00CC66']
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.4,
            textinfo='label+percent',
            textposition='outside'
        )])
        fig.update_layout(
            title='Distribuição de Níveis de Risco',
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def show_enhanced_risk_table(self, risk_df: pd.DataFrame):
        if risk_df.empty:
            st.info("📋 Nenhum dado disponível")
            return

        table_data = []
        for _, row in risk_df.iterrows():
            table_data.append({
                'Status': row.get('emoji_risco', '⚪'),
                'Medicamento': row.get('medicamento', 'N/A'),
                'Estoque Atual': f"{int(row.get('estoque_atual', 0)):,}".replace(',', '.'),
                'Consumo Previsto (3m)': f"{int(row.get('consumo_previsto', 0)):,}".replace(',', '.'),
                'Déficit': f"{int(row.get('deficit', 0)):,}".replace(',', '.') if row.get('deficit', 0) > 0 else '-',
                'Razão Estoque/Previsão': f"{row.get('razao_estoque', 0):.2f}x",
                'Nível': row.get('nivel_risco', 'N/A')
            })
        
        result_df = pd.DataFrame(table_data)
        st.dataframe(
            result_df,
            use_container_width=True,
            height=min(450, len(result_df) * 35 + 38)
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total de Registros",
                len(result_df)
            )
        with col2:
            total_deficit = risk_df['deficit'].sum() if 'deficit' in risk_df.columns else 0
            st.metric(
                "Déficit Total",
                f"{int(total_deficit):,}".replace(',', '.')
            )
        with col3:
            media_razao = risk_df['razao_estoque'].mean() if 'razao_estoque' in risk_df.columns else 0
            st.metric(
                "Razão Média",
                f"{media_razao:.2f}x"
            )
    
    def show_risk_table(self, risk_df: pd.DataFrame):
        if risk_df.empty:
            st.info("Nenhum dado disponível")
            return
 
        display_cols = ['emoji_risco', 'medicamento', 'estoque_atual', 
                       'consumo_previsto', 'deficit', 'nivel_risco']

        available_cols = [col for col in display_cols if col in risk_df.columns]
        table_df = risk_df[available_cols].copy()
        column_mapping = {
            'emoji_risco': 'Status',
            'medicamento': 'Medicamento',
            'estoque_atual': 'Estoque',
            'consumo_previsto': 'Prev. 3 Meses',
            'deficit': 'Déficit',
            'nivel_risco': 'Nível de Risco'
        }
        
        table_df = table_df.rename(columns={k: v for k, v in column_mapping.items() if k in table_df.columns})

        for col in ['Estoque', 'Prev. 3 Meses', 'Déficit']:
            if col in table_df.columns:
                table_df[col] = table_df[col].apply(lambda x: f"{int(x):,}".replace(',', '.'))

        def highlight_risk(row):
            if 'Nível de Risco' in row:
                risk = row['Nível de Risco']
                if risk == 'Alto':
                    return ['background-color: #FFE5E5'] * len(row)
                elif risk == 'Médio':
                    return ['background-color: #FFF4E5'] * len(row)
                else:
                    return ['background-color: #E5F9F0'] * len(row)
            return [''] * len(row)
        st.dataframe(
            table_df.style.apply(highlight_risk, axis=1),
            use_container_width=True,
            height=400
        )
    
    def plot_deficit_ranking(self, risk_df: pd.DataFrame, top_n: int = 10):
        if risk_df.empty or 'deficit' not in risk_df.columns:
            st.warning("Dados insuficientes para o gráfico")
            return
        deficit_df = risk_df[risk_df['deficit'] > 0].copy()
        
        if deficit_df.empty:
            st.success("Nenhum medicamento com déficit!")
            return
        deficit_df = deficit_df.sort_values('deficit', ascending=True).tail(top_n)
        colors = deficit_df['nivel_risco'].map({
            'Alto': '#FF4B4B',
            'Médio': '#FFA500',
            'Baixo': '#00CC66'
        })
        fig = go.Figure(data=[
            go.Bar(
                x=deficit_df['deficit'],
                y=deficit_df['medicamento'],
                orientation='h',
                marker=dict(color=colors),
                text=deficit_df['deficit'].apply(lambda x: f"{int(x):,}".replace(',', '.')),
                textposition='outside'
            )
        ])
        fig.update_layout(
            title=f'Top {top_n} Medicamentos por Déficit',
            xaxis_title='Déficit (unidades)',
            yaxis_title='',
            height=max(350, top_n * 35),
            template='plotly_white',
            showlegend=False
        )       
        st.plotly_chart(fig, use_container_width=True)
    
    def plot_top_medications(self, df: pd.DataFrame, metric: str = 'consumo', top_n: int = 10):
        if df.empty or metric not in df.columns:
            st.warning("Dados insuficientes para o gráfico")
            return

        top_df = df.groupby('medicamento')[metric].sum().sort_values(ascending=False).head(top_n)
        fig = go.Figure(data=[
            go.Bar(
                x=top_df.values,
                y=top_df.index,
                orientation='h',
                marker=dict(color=self.colors['primary'])
            )
        ])
        fig.update_layout(
            title=f'Top {top_n} Medicamentos por {metric.capitalize()}',
            xaxis_title=metric.capitalize(),
            yaxis_title='Medicamento',
            height=400,
            template='plotly_white'
        )       
        st.plotly_chart(fig, use_container_width=True)
    
    def plot_model_metrics(self, metrics: Dict):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mae = metrics.get('test_mae', 0)
            st.metric(
                label="MAE (Erro Médio Absoluto)",
                value=f"{mae:.0f}",
                help="Quanto menor, melhor"
            )
        
        with col2:
            rmse = metrics.get('test_rmse', 0)
            st.metric(
                label="RMSE (Raiz do Erro Quadrático)",
                value=f"{rmse:.0f}",
                help="Quanto menor, melhor"
            )
        
        with col3:
            r2 = metrics.get('test_r2', 0)
            st.metric(
                label="R² (Coeficiente de Determinação)",
                value=f"{r2:.3f}",
                help="Quanto mais próximo de 1, melhor"
            )
    
    def show_filters(self) -> Dict:
        st.sidebar.header("🔍 Filtros")
        filters = {}
        st.sidebar.subheader("Período")
        filters['months_history'] = st.sidebar.slider(
            "Meses de histórico",
            min_value=6,
            max_value=24,
            value=12,
            step=3
        )
        st.sidebar.subheader("Predição")
        filters['months_prediction'] = st.sidebar.slider(
            "Meses a prever",
            min_value=1,
            max_value=6,
            value=3,
            step=1
        )
        st.sidebar.subheader("Nível de Risco")
        filters['risk_filter'] = st.sidebar.multiselect(
            "Filtrar por risco",
            options=['Alto', 'Médio', 'Baixo'],
            default=['Alto', 'Médio', 'Baixo']
        )
        
        return filters
    
    def show_header(self):
        st.title("🏥 Sistema Preditivo de Escassez de Medicamentos")
        st.markdown("""
        Dashboard interativo para monitoramento e previsão de consumo de medicamentos essenciais,
        utilizando Machine Learning e dados do DATASUS.
        """)
        st.divider()
    
    def show_footer(self):
        st.divider()
        st.markdown("""
        ---
        **Fonte de Dados:** DATASUS (SIA/SUS) | **Modelo:** Random Forest Regressor | 
        **Desenvolvido para:** Apoio à Gestão de Saúde Pública
        
        *Os dados utilizados são agregados e anônimos, em conformidade com a LGPD.*
        """)
