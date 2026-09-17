"""Chronological recursive holdout evaluation, followed by a full-history fit."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.features.engineering import FEATURE_COLUMNS, FeatureEngineer


def make_model():
    return RandomForestRegressor(
        n_estimators=100, max_depth=8, min_samples_leaf=2, random_state=42, n_jobs=-1
    )


def forecast(model, history: pd.DataFrame, months: int) -> pd.DataFrame:
    """Recompute lagged inputs after each prediction; never use future observations."""
    working = history.copy()
    rows = []
    for _ in range(months):
        last = working.iloc[-1]
        date = str(pd.Period(last["data"], freq="M") + 1)
        future = {
            "unidade": last["unidade"],
            "medicamento": last["medicamento"],
            "data": date,
            "consumo": np.nan,
            "estoque_atual": np.nan,
        }
        extended = pd.concat([working, pd.DataFrame([future])], ignore_index=True)
        features = FeatureEngineer().create_features(extended).iloc[[-1]]
        value = max(0.0, float(model.predict(features[FEATURE_COLUMNS])[0]))
        rows.append({**future, "consumo_previsto": value})
        extended.loc[extended.index[-1], "consumo"] = value
        working = extended
    return pd.DataFrame(rows)[["unidade", "medicamento", "data", "consumo_previsto"]]


def train_and_evaluate(history: pd.DataFrame, horizon: int):
    """One model per unit/medicine. Holdout equals the selected forecast horizon."""
    if len(history) < 9 + horizon:
        raise ValueError(
            f"São necessários pelo menos {9 + horizon} meses para avaliar esse horizonte."
        )
    train, test = history.iloc[:-horizon], history.iloc[-horizon:]
    features = FeatureEngineer().create_features(train).dropna(subset=FEATURE_COLUMNS)
    model = make_model()
    model.fit(features[FEATURE_COLUMNS], features["consumo"])
    predicted = forecast(model, train, horizon)["consumo_previsto"].to_numpy()
    actual = test["consumo"].to_numpy()
    baseline = np.repeat(train["consumo"].iloc[-1], horizon)
    metrics = {
        "unidade": history["unidade"].iloc[0],
        "medicamento": history["medicamento"].iloc[0],
        "mae": mean_absolute_error(actual, predicted),
        "rmse": np.sqrt(mean_squared_error(actual, predicted)),
        "r2": r2_score(actual, predicted) if horizon > 1 and np.var(actual) > 0 else np.nan,
        "mae_baseline": mean_absolute_error(actual, baseline),
        "treino_ate": train["data"].iloc[-1],
        "teste_de": test["data"].iloc[0],
        "teste_ate": test["data"].iloc[-1],
        "meses_teste": horizon,
    }
    all_features = FeatureEngineer().create_features(history).dropna(subset=FEATURE_COLUMNS)
    model.fit(all_features[FEATURE_COLUMNS], all_features["consumo"])
    return model, metrics
