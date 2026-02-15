import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
from typing import Tuple, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class MedicationPredictor:
    def __init__(self, n_estimators: int = 100, max_depth: int = 10, random_state: int = 42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
            min_samples_split=5,
            min_samples_leaf=2
        )
        self.feature_names = []
        self.metrics = {}
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        exclude_cols = ['medicamento', 'data', 'consumo', 'estoque_atual', 'data_dt']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        X = df[feature_cols].copy()
        y = df['consumo'].copy()
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        
        self.feature_names = feature_cols
        
        return X, y
    
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Dict[str, float]:
        print("Iniciando treinamento do modelo...")

        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        self.model.fit(X_train, y_train)

        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)

        self.metrics = {
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'test_r2': r2_score(y_test, y_pred_test)
        }
        
        print(f"Treinamento concluído")
        print(f"  - MAE (teste): {self.metrics['test_mae']:.2f}")
        print(f"  - RMSE (teste): {self.metrics['test_rmse']:.2f}")
        print(f"  - R² (teste): {self.metrics['test_r2']:.3f}")
        
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X = X[self.feature_names] if self.feature_names else X
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        
        predictions = self.model.predict(X)
        predictions = np.maximum(predictions, 0)
        
        return predictions
    
    def get_feature_importance(self) -> pd.DataFrame:
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        })
        
        importance_df = importance_df.sort_values('importance', ascending=False)
        
        return importance_df
    
    def save_model(self, filepath: str):
        try:
            with open(filepath, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'feature_names': self.feature_names,
                    'metrics': self.metrics
                }, f)
            print(f"Modelo salvo em {filepath}")
        except Exception as e:
            print(f"Erro ao salvar modelo: {e}")
    
    def load_model(self, filepath: str):
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.feature_names = data['feature_names']
                self.metrics = data['metrics']
            print(f"✓ Modelo carregado de {filepath}")
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")


def train_medication_model(df: pd.DataFrame) -> Tuple[MedicationPredictor, Dict[str, float]]:
    predictor = MedicationPredictor()
    X, y = predictor.prepare_data(df)
    metrics = predictor.train(X, y)
    
    return predictor, metrics
