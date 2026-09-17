"""Application service shared by standalone and authenticated dashboards."""

from dataclasses import dataclass

import pandas as pd

from src.models.predict import analyze_series
from src.models.risk_classifier import RiskClassifier
from src.preprocessing.cleaning import DataCleaner


@dataclass
class Analysis:
    history: pd.DataFrame
    predictions: pd.DataFrame
    risks: pd.DataFrame
    metrics: pd.DataFrame
    skipped: list[str]


def analyze(raw: pd.DataFrame, months: int = 3, safety: float = 0.2) -> Analysis:
    if months not in range(1, 7):
        raise ValueError("Selecione um horizonte de 1 a 6 meses.")
    history = DataCleaner().clean(raw)
    predictions, metrics, skipped = analyze_series(history, months)
    keys = ["unidade", "medicamento"]
    # tail preserves missing stock in the latest snapshot; groupby.last skips it.
    stock = history.sort_values("data").groupby(keys).tail(1)[keys + ["estoque_atual", "data"]]
    stock = stock.rename(columns={"data": "data_estoque"})
    demand = predictions.groupby(keys, as_index=False)["consumo_previsto"].sum()
    risks = RiskClassifier(safety).classify_batch(demand.merge(stock, on=keys))
    return Analysis(history, predictions, risks, metrics, skipped)
