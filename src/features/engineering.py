import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.helpers import calculate_statistics


class FeatureEngineer:
    def __init__(self):
        self.features = []
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        print("Criando features preditivas...")
        
        df_features = df.copy()
        
        df_features['data_dt'] = pd.to_datetime(df_features['data'] + '-01')
        
        df_features = df_features.sort_values('data_dt').reset_index(drop=True)
        
        df_features = self._add_temporal_features(df_features)
        
        df_features = self._add_statistical_features(df_features)
        
        df_features = self._add_trend_features(df_features)
        
        df_features = self._add_seasonality_features(df_features)
        
        df_features = self._add_moving_averages(df_features)
        
        df_features = self._add_derived_features(df_features)
        
        df_features = df_features.drop('data_dt', axis=1)
        
        print(f"Features criadas: {len(df_features.columns)} colunas")
        
        return df_features
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df['mes'] = df['data_dt'].dt.month
        df['trimestre'] = df['data_dt'].dt.quarter
        df['ano'] = df['data_dt'].dt.year
        df['mes_idx'] = (df['ano'] - df['ano'].min()) * 12 + df['mes']
        
        return df
    
    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:

        df['consumo_media_3m'] = df['consumo'].rolling(window=3, min_periods=1).mean()
        df['consumo_std_3m'] = df['consumo'].rolling(window=3, min_periods=1).std().fillna(0)
        
        df['consumo_media_6m'] = df['consumo'].rolling(window=6, min_periods=1).mean()
        df['consumo_std_6m'] = df['consumo'].rolling(window=6, min_periods=1).std().fillna(0)
        
        df['consumo_media_12m'] = df['consumo'].rolling(window=12, min_periods=1).mean()
        df['consumo_max_12m'] = df['consumo'].rolling(window=12, min_periods=1).max()
        df['consumo_min_12m'] = df['consumo'].rolling(window=12, min_periods=1).min()
        
        return df
    
    def _add_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        window = 12
        trends = []
        
        for i in range(len(df)):
            if i < window - 1:
                trends.append(0)
            else:
                y = df['consumo'].iloc[i-window+1:i+1].values
                X = np.arange(window).reshape(-1, 1)
                
                try:
                    lr = LinearRegression()
                    lr.fit(X, y)
                    trend = lr.coef_[0]
                    trends.append(trend)
                except:
                    trends.append(0)
        
        df['tendencia_12m'] = trends
        
        df['tendencia_3m'] = df['consumo'].diff(3).fillna(0)
        
        return df
    
    def _add_seasonality_features(self, df: pd.DataFrame) -> pd.DataFrame:

        monthly_avg = df.groupby('mes')['consumo'].transform('mean')
        df['sazonalidade_mes'] = monthly_avg
        
        df['razao_sazonal'] = df['consumo'] / (df['sazonalidade_mes'] + 1)
        
        df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
        df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
        
        return df
    
    def _add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:

        df['ma_3'] = df['consumo'].rolling(window=3, min_periods=1).mean()
        df['ma_6'] = df['consumo'].rolling(window=6, min_periods=1).mean()     
        df['ema_3'] = df['consumo'].ewm(span=3, adjust=False).mean()
        df['ema_6'] = df['consumo'].ewm(span=6, adjust=False).mean()
        
        return df
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df['variacao_mensal'] = df['consumo'].pct_change().fillna(0)
        df['variacao_mensal'] = df['variacao_mensal'].replace([np.inf, -np.inf], 0)   
        df['aceleracao'] = df['variacao_mensal'].diff().fillna(0)       
        df['cv_3m'] = (df['consumo_std_3m'] / (df['consumo_media_3m'] + 1)) * 100
        df['cv_6m'] = (df['consumo_std_6m'] / (df['consumo_media_6m'] + 1)) * 100        
        df['desvio_ma3'] = df['consumo'] - df['ma_3']
        df['desvio_ma6'] = df['consumo'] - df['ma_6']        
        df['crescimento'] = (df['consumo'] > df['ma_6']).astype(int)      
        df['volatilidade'] = df['consumo'].rolling(window=6, min_periods=1).std().fillna(0)
        
        return df
    
    def get_feature_importance(self, df: pd.DataFrame) -> Dict[str, float]:
        exclude_cols = ['medicamento', 'data', 'data_dt', 'consumo', 'estoque_atual']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        importance = {}
        
        for col in feature_cols:
            try:
                corr = df[['consumo', col]].corr().iloc[0, 1]
                importance[col] = abs(corr) if not np.isnan(corr) else 0
            except:
                importance[col] = 0
        
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        return importance
    
    def select_top_features(self, df: pd.DataFrame, n_features: int = 15) -> List[str]:
        importance = self.get_feature_importance(df)
        top_features = list(importance.keys())[:n_features]
        
        print(f"✓ Selecionadas {len(top_features)} features mais importantes")
        
        return top_features
    
    def prepare_for_training(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(0)
        
        return df
