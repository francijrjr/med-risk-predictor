import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.ingestion.datasus_client import DataSUSClient


class DataLoader:
    def __init__(self, data_dir: str = 'data/samples'):
        self.data_dir = Path(data_dir)
        self.datasus_client = DataSUSClient()
    
    def load_data(self, source: str = 'auto') -> pd.DataFrame:
        if source == 'datasus':
            return self._load_from_datasus()
        elif source == 'local':
            return self._load_from_local()
        else:  
            df = self._load_from_datasus()
            if df is not None and not df.empty:
                print("Dados carregados do DATASUS")
                return df
            
            df = self._load_from_local()
            if df is not None and not df.empty:
                print("Dados carregados de arquivo local")
                return df
            
            print("Usando dados simulados (DATASUS indisponível)")
            return self._generate_sample_data()
    
    def _load_from_datasus(self) -> Optional[pd.DataFrame]:
        try:
            if not self.datasus_client.test_connection():
                print("DATASUS não acessível")
                return None
            params = {
                'uf': 'SP',
                'year': '2024',
                'month': '01'
            }
            
            df = self.datasus_client.fetch_medication_data(params)
            return df
            
        except Exception as e:
            print(f"Erro ao carregar do DATASUS: {e}")
            return None
    
    def _load_from_local(self) -> Optional[pd.DataFrame]:
        try:
            csv_path = self.data_dir / 'datasus_sample.csv'
            
            if not csv_path.exists():
                print(f"Arquivo não encontrado: {csv_path}")
                return None
            
            df = pd.read_csv(csv_path)

            required_cols = ['medicamento', 'data', 'consumo', 'estoque_atual']
            if not all(col in df.columns for col in required_cols):
                print(f"Arquivo CSV inválido. Colunas esperadas: {required_cols}")
                return None
            
            return df
            
        except Exception as e:
            print(f"Erro ao carregar arquivo local: {e}")
            return None
    
    def _generate_sample_data(self) -> pd.DataFrame:
        np.random.seed(42)
        medicamentos = [
            'Paracetamol 500mg',
            'Ibuprofeno 600mg',
            'Amoxicilina 500mg',
            'Dipirona 500mg',
            'Losartana 50mg',
            'Metformina 850mg',
            'Omeprazol 20mg',
            'Captopril 25mg',
            'Atenolol 25mg',
            'Sinvastatina 20mg'
        ]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730) 
        
        data = []
        
        for medicamento in medicamentos:
            base_consumo = np.random.randint(1000, 5000)
            current_date = start_date
            
            for i in range(24):
                mes = current_date.month
                fator_sazonal = 1.3 if mes in [5, 6, 7, 8] else 1.0
                fator_tendencia = 1 + (i * 0.01)
                fator_ruido = np.random.uniform(0.8, 1.2)
                consumo = int(base_consumo * fator_sazonal * fator_tendencia * fator_ruido)
                estoque = int(consumo * np.random.uniform(0.8, 1.5))
                
                data.append({
                    'medicamento': medicamento,
                    'data': current_date.strftime('%Y-%m'),
                    'consumo': consumo,
                    'estoque_atual': estoque
                })

                current_date = current_date + timedelta(days=30)
        
        df = pd.DataFrame(data)
        df = df.sort_values(['medicamento', 'data']).reset_index(drop=True)
        
        print(f"Gerados {len(df)} registros simulados para {len(medicamentos)} medicamentos")
        
        return df
    
    def save_sample_data(self, df: pd.DataFrame, filename: str = 'datasus_sample.csv'):
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            filepath = self.data_dir / filename
            df.to_csv(filepath, index=False)
            print(f"Dados salvos em {filepath}")
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
    
    def get_data_info(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty:
            return {}
        
        return {
            'total_registros': len(df),
            'medicamentos_unicos': df['medicamento'].nunique(),
            'periodo_inicio': df['data'].min(),
            'periodo_fim': df['data'].max(),
            'consumo_total': df['consumo'].sum(),
            'estoque_total': df['estoque_atual'].sum()
        }
