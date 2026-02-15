import requests
import pandas as pd
import io
from typing import Optional, Dict
import time


class DataSUSClient:
    BASE_URLS = {
        'sia': 'http://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/',
        'sih': 'http://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/',
        'cnes': 'http://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/'
    }
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_sia_data(self, uf: str, year: str, month: str) -> Optional[pd.DataFrame]:
        try:
            file_code = f"PA{uf}{year[2:]}{month}"
            url = f"{self.BASE_URLS['sia']}{file_code}.dbf"
            
            print(f"Tentando baixar dados do DATASUS: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            print("Dados do DATASUS não disponíveis no formato esperado.")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar DATASUS: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado ao processar dados do DATASUS: {e}")
            return None
    
    def fetch_medication_data(self, params: Dict[str, str]) -> Optional[pd.DataFrame]:
        try:
            df = self.fetch_sia_data(
                params.get('uf', 'SP'),
                params.get('year', '2024'),
                params.get('month', '01')
            )
            
            if df is not None:
                return self._process_datasus_data(df)
            
            return None
            
        except Exception as e:
            print(f"Erro ao buscar dados de medicamentos: {e}")
            return None
    
    def _process_datasus_data(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            processed = pd.DataFrame({
                'medicamento': df['PA_PROC'] if 'PA_PROC' in df.columns else 'N/A',
                'data': df['PA_COMPET'] if 'PA_COMPET' in df.columns else 'N/A',
                'consumo': df['PA_QTDPRO'] if 'PA_QTDPRO' in df.columns else 0,
                'estoque_atual': 0  
            })
            
            return processed
            
        except Exception as e:
            print(f"Erro ao processar dados do DATASUS: {e}")
            return pd.DataFrame()
    
    def test_connection(self) -> bool:
        try:
            response = self.session.head(
                self.BASE_URLS['sia'],
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_available_periods(self) -> list:
        return [
            '2024-01', '2024-02', '2024-03', '2024-04',
            '2024-05', '2024-06', '2024-07', '2024-08',
            '2024-09', '2024-10', '2024-11', '2024-12'
        ]
    
    def close(self):
        self.session.close()
