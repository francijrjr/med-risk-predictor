import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    if df is None or df.empty:
        return False
    
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        print(f"Colunas faltando: {missing_columns}")
        return False
    
    return True

def format_date(date_str: str) -> str:
    try:
        if isinstance(date_str, str):
            for fmt in ['%Y-%m', '%Y/%m', '%Y%m', '%d/%m/%Y', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m')
                except ValueError:
                    continue
        elif isinstance(date_str, (datetime, pd.Timestamp)):
            return date_str.strftime('%Y-%m')
    except Exception as e:
        print(f"Erro ao formatar data '{date_str}': {e}")
    
    return date_str

def calculate_growth_rate(series: pd.Series) -> float:
    if len(series) < 2:
        return 0.0
    
    try:
        first_value = series.iloc[0]
        last_value = series.iloc[-1]
        
        if first_value == 0:
            return 0.0
        
        growth_rate = ((last_value - first_value) / first_value) * 100
        return round(growth_rate, 2)
    except Exception:
        return 0.0


def generate_date_range(start_date: str, periods: int) -> List[str]:
    try:
        start = datetime.strptime(start_date, '%Y-%m')
        dates = []
        
        for i in range(periods):
            current_date = start + timedelta(days=30 * i)
            dates.append(current_date.strftime('%Y-%m'))
        
        return dates
    except Exception as e:
        print(f"Erro ao gerar range de datas: {e}")
        return []


def calculate_statistics(series: pd.Series) -> Dict[str, float]:
    if series.empty:
        return {
            'mean': 0.0,
            'median': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'cv': 0.0
        }
    
    stats = {
        'mean': round(series.mean(), 2),
        'median': round(series.median(), 2),
        'std': round(series.std(), 2),
        'min': round(series.min(), 2),
        'max': round(series.max(), 2)
    }

    if stats['mean'] != 0:
        stats['cv'] = round((stats['std'] / stats['mean']) * 100, 2)
    else:
        stats['cv'] = 0.0
    
    return stats


def clean_numeric_column(series: pd.Series) -> pd.Series:
    series = series.astype(str).str.replace(',', '.').str.strip()
    series = pd.to_numeric(series, errors='coerce')
    series = series.fillna(0)
    
    return series

def get_risk_color(risk_level: str) -> str:
    colors = {
        'Alto': '#FF4B4B',
        'Médio': '#FFA500',
        'Baixo': '#00CC66'
    }
    
    return colors.get(risk_level, '#CCCCCC')


def get_risk_emoji(risk_level: str) -> str:
    emojis = {
        'Alto': '🔴',
        'Médio': '🟡',
        'Baixo': '🟢'
    }
    
    return emojis.get(risk_level, '⚪')


def format_number(value: float, decimals: int = 2) -> str:
    try:
        return f"{value:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception:
        return str(value)


def create_month_mapping() -> Dict[int, str]:
    return {
        1: 'Janeiro',
        2: 'Fevereiro',
        3: 'Março',
        4: 'Abril',
        5: 'Maio',
        6: 'Junho',
        7: 'Julho',
        8: 'Agosto',
        9: 'Setembro',
        10: 'Outubro',
        11: 'Novembro',
        12: 'Dezembro'
    }


def get_last_n_months(n: int, from_date: str = None) -> List[str]:
    if from_date is None:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(from_date, '%Y-%m')
    
    months = []
    for i in range(n):
        month_date = end_date - timedelta(days=30 * i)
        months.append(month_date.strftime('%Y-%m'))
    
    return sorted(months)


def calculate_percentage(part: float, total: float) -> float:
    if total == 0:
        return 0.0
    
    return round((part / total) * 100, 2)
