import pandas as pd
import numpy as np
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.helpers import get_risk_color, get_risk_emoji


class RiskClassifier:
    RISK_LEVELS = {
        'Alto': {'threshold_min': 0, 'threshold_max': 1.0, 'color': '#FF4B4B', 'emoji': '🔴'},
        'Médio': {'threshold_min': 1.0, 'threshold_max': 1.2, 'color': '#FFA500', 'emoji': '🟡'},
        'Baixo': {'threshold_min': 1.2, 'threshold_max': float('inf'), 'color': '#00CC66', 'emoji': '🟢'}
    }
    
    def __init__(self):
        pass
    
    def classify_risk(self, estoque: float, previsao: float) -> str:
       
        if previsao == 0:
            return 'Baixo'  
        razao = estoque / previsao   
        if razao < 1.0:
            return 'Alto'
        elif razao < 1.2:
            return 'Médio'
        else:
            return 'Baixo'
    
    def classify_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['nivel_risco'] = df.apply(
            lambda row: self.classify_risk(
                row.get('estoque_atual', 0),
                row.get('consumo_previsto', 0)
            ),
            axis=1
        )

        df['cor_risco'] = df['nivel_risco'].apply(get_risk_color)
        df['emoji_risco'] = df['nivel_risco'].apply(get_risk_emoji)
        df['razao_estoque'] = df.apply(
            lambda row: round(row['estoque_atual'] / row['consumo_previsto'], 2)
            if row.get('consumo_previsto', 0) > 0 else 0,
            axis=1
        )      
        df['deficit'] = df.apply(
            lambda row: max(0, row.get('consumo_previsto', 0) - row.get('estoque_atual', 0)),
            axis=1
        )
        
        return df
    
    def get_risk_statistics(self, df: pd.DataFrame) -> Dict[str, int]:
        if df.empty or 'nivel_risco' not in df.columns:
            return {'Alto': 0, 'Médio': 0, 'Baixo': 0}
        
        risk_counts = df['nivel_risco'].value_counts().to_dict()
        stats = {
            'Alto': risk_counts.get('Alto', 0),
            'Médio': risk_counts.get('Médio', 0),
            'Baixo': risk_counts.get('Baixo', 0)
        }
        
        return stats
    
    def get_high_risk_medications(self, df: pd.DataFrame) -> pd.DataFrame:

        if df.empty or 'nivel_risco' not in df.columns:
            return pd.DataFrame()
        
        high_risk = df[df['nivel_risco'] == 'Alto'].copy()

        if not high_risk.empty and 'deficit' in high_risk.columns:
            high_risk = high_risk.sort_values('deficit', ascending=False)
        
        return high_risk
    
    def get_priority_list(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:

        if df.empty or 'nivel_risco' not in df.columns:
            return pd.DataFrame()

        priority = df[df['nivel_risco'].isin(['Alto', 'Médio'])].copy()
        risk_order = {'Alto': 1, 'Médio': 2, 'Baixo': 3}
        priority['risk_order'] = priority['nivel_risco'].map(risk_order)
        priority = priority.sort_values(
            ['risk_order', 'deficit'],
            ascending=[True, False]
        )
        priority = priority.drop('risk_order', axis=1)
        
        return priority.head(top_n)
    
    def generate_alert_message(self, row: pd.Series) -> str:
        medicamento = row.get('medicamento', 'Desconhecido')
        nivel = row.get('nivel_risco', 'Desconhecido')
        estoque = row.get('estoque_atual', 0)
        previsao = row.get('consumo_previsto', 0)
        deficit = row.get('deficit', 0)
        emoji = row.get('emoji_risco', '⚪')
        
        if nivel == 'Alto':
            return (f"{emoji} ALERTA: {medicamento} - Estoque insuficiente! "
                   f"Estoque: {estoque:.0f} | Previsão: {previsao:.0f} | "
                   f"Déficit: {deficit:.0f}")
        elif nivel == 'Médio':
            return (f"{emoji} ATENÇÃO: {medicamento} - Estoque baixo. "
                   f"Estoque: {estoque:.0f} | Previsão: {previsao:.0f}")
        else:
            return (f"{emoji} OK: {medicamento} - Estoque adequado. "
                   f"Estoque: {estoque:.0f} | Previsão: {previsao:.0f}")
    
    def create_risk_report(self, df: pd.DataFrame) -> Dict:
        stats = self.get_risk_statistics(df)
        high_risk = self.get_high_risk_medications(df)
        priority = self.get_priority_list(df)
        
        total = len(df)
        
        report = {
            'total_medicamentos': total,
            'estatisticas': stats,
            'percentual_alto': round((stats['Alto'] / total * 100), 1) if total > 0 else 0,
            'percentual_medio': round((stats['Médio'] / total * 100), 1) if total > 0 else 0,
            'percentual_baixo': round((stats['Baixo'] / total * 100), 1) if total > 0 else 0,
            'medicamentos_alto_risco': high_risk.to_dict('records') if not high_risk.empty else [],
            'lista_prioridade': priority.to_dict('records') if not priority.empty else [],
            'deficit_total': df['deficit'].sum() if 'deficit' in df.columns else 0
        }
        
        return report


def classify_medication_risk(predictions: pd.DataFrame, current_stock: pd.DataFrame) -> pd.DataFrame:
    risk_df = predictions.merge(
        current_stock[['medicamento', 'estoque_atual']],
        on='medicamento',
        how='left'
    )
    risk_df['estoque_atual'] = risk_df['estoque_atual'].fillna(0)
    classifier = RiskClassifier()
    risk_df = classifier.classify_batch(risk_df)
    
    return risk_df
