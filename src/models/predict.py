import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.features.engineering import FeatureEngineer


class ConsumptionPredictor:
    def __init__(self, model, feature_engineer: FeatureEngineer):
        self.model = model
        self.feature_engineer = feature_engineer
    
    def predict_future(self, df: pd.DataFrame, medicamento: str, n_months: int = 3) -> pd.DataFrame:
        med_data = df[df['medicamento'] == medicamento].copy()
        
        if med_data.empty:
            print(f"Nenhum dado encontrado para {medicamento}")
            return pd.DataFrame()

        med_data = med_data.sort_values('data').reset_index(drop=True)
        last_date = pd.to_datetime(med_data['data'].iloc[-1] + '-01')
        
        predictions = []
        
        for i in range(1, n_months + 1):
            future_date = last_date + timedelta(days=30 * i)
            future_date_str = future_date.strftime('%Y-%m')
            future_features = self._create_future_features(med_data, future_date)
            pred = self.model.predict(future_features)
            pred_value = max(0, pred[0])  
            predictions.append({
                'medicamento': medicamento,
                'data': future_date_str,
                'consumo_previsto': round(pred_value, 0),
                'tipo': 'predição'
            })
            new_row = future_features.copy()
            new_row['consumo'] = pred_value
            new_row['data'] = future_date_str
            new_row['medicamento'] = medicamento
            med_data = pd.concat([med_data, new_row], ignore_index=True)
            med_data = self.feature_engineer.create_features(med_data)
        
        return pd.DataFrame(predictions)
    
    def _create_future_features(self, historical_data: pd.DataFrame, future_date: datetime) -> pd.DataFrame:
        last_row = historical_data.iloc[[-1]].copy()
        last_row['mes'] = future_date.month
        last_row['trimestre'] = (future_date.month - 1) // 3 + 1
        last_row['ano'] = future_date.year

        if 'mes_idx' in last_row.columns:
            last_row['mes_idx'] = last_row['mes_idx'] + 1

        if 'mes_sin' in last_row.columns:
            last_row['mes_sin'] = np.sin(2 * np.pi * future_date.month / 12)
        if 'mes_cos' in last_row.columns:
            last_row['mes_cos'] = np.cos(2 * np.pi * future_date.month / 12)
        
        return last_row
    
    def predict_all_medications(self, df: pd.DataFrame, n_months: int = 3) -> pd.DataFrame:
        all_predictions = []
        
        medicamentos = df['medicamento'].unique()
        
        print(f"Gerando predições para {len(medicamentos)} medicamentos...")
        
        for med in medicamentos:
            try:
                pred_df = self.predict_future(df, med, n_months)
                if not pred_df.empty:
                    all_predictions.append(pred_df)
            except Exception as e:
                print(f"Erro ao prever {med}: {e}")
        
        if all_predictions:
            result = pd.concat(all_predictions, ignore_index=True)
            print(f"✓ Predições geradas: {len(result)} registros")
            return result
        
        return pd.DataFrame()
    
    def get_prediction_summary(self, predictions: pd.DataFrame, historical: pd.DataFrame) -> Dict:

        if predictions.empty:
            return {}
        
        summary = {
            'total_predicoes': len(predictions),
            'medicamentos': predictions['medicamento'].nunique(),
            'consumo_previsto_total': predictions['consumo_previsto'].sum(),
            'consumo_medio_previsto': predictions['consumo_previsto'].mean(),
            'maior_consumo_previsto': predictions['consumo_previsto'].max(),
            'menor_consumo_previsto': predictions['consumo_previsto'].min()
        }

        if not historical.empty:
            avg_historical = historical['consumo'].mean()
            avg_predicted = predictions['consumo_previsto'].mean()
            summary['variacao_vs_historico'] = ((avg_predicted - avg_historical) / avg_historical) * 100
        
        return summary


def make_predictions(df_with_features: pd.DataFrame, model, n_months: int = 3) -> pd.DataFrame:
    feature_engineer = FeatureEngineer()
    predictor = ConsumptionPredictor(model, feature_engineer)
    
    predictions = predictor.predict_all_medications(df_with_features, n_months)
    
    return predictions
