import pandas as pd
import numpy as np
from typing import Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.helpers import validate_dataframe, format_date, clean_numeric_column

class DataCleaner:
    def __init__(self):
        self.required_columns = ['medicamento', 'data', 'consumo', 'estoque_atual']
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            print("DataFrame vazio recebido")
            return pd.DataFrame()
        
        print(f"Iniciando limpeza de {len(df)} registros...")

        df = self._validate_structure(df)
        df = self._remove_duplicates(df)
        df = self._handle_missing_values(df)
        df = self._clean_columns(df)
        df = self._normalize_dates(df)
        df = self._remove_outliers(df)
        df = self._sort_data(df)
        
        print(f"Limpeza concluída: {len(df)} registros válidos")
        
        return df
    
    def _validate_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        if not validate_dataframe(df, self.required_columns):
            raise ValueError(f"DataFrame inválido. Colunas necessárias: {self.required_columns}")
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        initial_len = len(df)
        df = df.drop_duplicates(subset=['medicamento', 'data'], keep='first')
        removed = initial_len - len(df)
        
        if removed > 0:
            print(f"  - Removidas {removed} duplicatas")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        initial_len = len(df)
        
        df = df.dropna(subset=['medicamento', 'data'])
        df['consumo'] = df['consumo'].fillna(0)
        df['estoque_atual'] = df['estoque_atual'].fillna(0)
        
        removed = initial_len - len(df)
        if removed > 0:
            print(f"Removidas {removed} linhas com valores críticos faltantes")
        
        return df
    
    def _clean_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df['medicamento'] = df['medicamento'].astype(str).str.strip().str.upper()
        df['consumo'] = clean_numeric_column(df['consumo'])
        df['estoque_atual'] = clean_numeric_column(df['estoque_atual'])
        df['consumo'] = df['consumo'].clip(lower=0)
        df['estoque_atual'] = df['estoque_atual'].clip(lower=0)
        
        return df
    
    def _normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        df['data'] = df['data'].apply(format_date)
        df = df[df['data'].str.match(r'^\d{4}-\d{2}$', na=False)]
        
        return df
    
    def _remove_outliers(self, df: pd.DataFrame, n_std: float = 3.0) -> pd.DataFrame:
        initial_len = len(df)
        
        for col in ['consumo', 'estoque_atual']:
            if col in df.columns:
                mean = df[col].mean()
                std = df[col].std()
                
                if std > 0:
                    upper_limit = mean + (n_std * std)
                    df = df[df[col] <= upper_limit]
        
        removed = initial_len - len(df)
        if removed > 0:
            print(f"Removidos {removed} outliers extremos")
        
        return df
    
    def _sort_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values(['medicamento', 'data']).reset_index(drop=True)
        return df
    
    def aggregate_monthly(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        print("Agregando dados mensalmente...")

        agg_dict = {
            'consumo': 'sum',
            'estoque_atual': 'mean'
        }
        
        df_agg = df.groupby(['medicamento', 'data']).agg(agg_dict).reset_index()
        df_agg['consumo'] = df_agg['consumo'].round(0).astype(int)
        df_agg['estoque_atual'] = df_agg['estoque_atual'].round(0).astype(int)
        
        print(f"Agregação concluída: {len(df_agg)} registros mensais")
        
        return df_agg
    
    def split_by_medication(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {}
        
        medicamentos = {}
        
        for med in df['medicamento'].unique():
            med_df = df[df['medicamento'] == med].copy()
            med_df = med_df.sort_values('data').reset_index(drop=True)
            medicamentos[med] = med_df
        
        return medicamentos
    
    def get_cleaning_summary(self, df_before: pd.DataFrame, df_after: pd.DataFrame) -> dict:
        return {
            'registros_iniciais': len(df_before) if df_before is not None else 0,
            'registros_finais': len(df_after) if df_after is not None else 0,
            'registros_removidos': len(df_before) - len(df_after) if df_before is not None and df_after is not None else 0,
            'taxa_retencao': round((len(df_after) / len(df_before) * 100), 2) if df_before is not None and len(df_before) > 0 else 0,
            'medicamentos_unicos': df_after['medicamento'].nunique() if df_after is not None and not df_after.empty else 0
        }
