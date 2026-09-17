"""Predictors known before the target month, calculated within each series."""

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "mes_sin",
    "mes_cos",
    "lag_1",
    "lag_2",
    "lag_3",
    "media_3m",
    "media_6m",
]
SERIES_COLUMNS = ["unidade", "medicamento"]


class FeatureEngineer:
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.sort_values(SERIES_COLUMNS + ["data"]).copy()
        month = pd.to_datetime(result["data"] + "-01").dt.month
        result["mes_sin"] = np.sin(2 * np.pi * month / 12)
        result["mes_cos"] = np.cos(2 * np.pi * month / 12)
        groups = result.groupby(SERIES_COLUMNS)["consumo"]
        for lag in (1, 2, 3):
            result[f"lag_{lag}"] = groups.shift(lag)
        for window in (3, 6):
            result[f"media_{window}m"] = groups.transform(
                lambda values, window=window: values.shift(1).rolling(window, min_periods=3).mean()
            )
        return result
