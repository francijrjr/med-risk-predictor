"""Run independent forecasts for each health unit and medication."""

import pandas as pd

from src.models.train import forecast, train_and_evaluate


def analyze_series(history: pd.DataFrame, months: int):
    predictions, metrics, skipped = [], [], []
    for (unit, medicine), group in history.groupby(["unidade", "medicamento"]):
        group = group.sort_values("data").reset_index(drop=True)
        if len(group) < 9 + months:
            skipped.append(f"{unit} / {medicine}: {len(group)} meses; mínimo {9 + months}.")
            continue
        model, evaluation = train_and_evaluate(group, months)
        predictions.append(forecast(model, group, months))
        metrics.append(evaluation)
    if not predictions:
        raise ValueError("Histórico insuficiente para avaliação temporal. " + " ".join(skipped[:3]))
    return pd.concat(predictions, ignore_index=True), pd.DataFrame(metrics), skipped
