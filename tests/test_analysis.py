import numpy as np
import pandas as pd
import pytest

from src.analysis import analyze
from src.features.engineering import FEATURE_COLUMNS, FeatureEngineer
from src.models.risk_classifier import RiskClassifier
from src.preprocessing.cleaning import DataCleaner


def history(months=24, name="MED A"):
    return pd.DataFrame(
        {
            "unidade": "PSF A",
            "medicamento": name,
            "data": pd.period_range("2023-01", periods=months, freq="M").astype(str),
            "consumo": np.arange(months) * 5 + 100,
            "estoque_atual": 400.0,
        }
    )


@pytest.mark.parametrize(
    "stock,demand,expected",
    [
        (121, 100, "Baixo"),
        (120, 100, "Médio"),
        (100, 100, "Médio"),
        (90, 100, "Alto"),
        (0, 100, "Alto"),
        (np.nan, 100, "Sem dados"),
        (0, 0, "Sem dados"),
        (100, 0, "Baixo"),
    ],
)
def test_tcc_risk(stock, demand, expected):
    assert RiskClassifier(0.2).classify_risk(stock, demand) == expected


def test_exact_high_boundary():
    classifier = RiskClassifier(0)
    assert classifier.classify_risk(100, 130) == "Médio"
    assert classifier.classify_risk(100, 130.01) == "Alto"


def test_current_and_future_consumption_cannot_change_past_features():
    raw = history()
    before = FeatureEngineer().create_features(raw)
    raw.loc[12:, "consumo"] = 999999
    after = FeatureEngineer().create_features(raw)
    pd.testing.assert_frame_equal(before.loc[:12, FEATURE_COLUMNS], after.loc[:12, FEATURE_COLUMNS])


def test_series_do_not_share_lags():
    first, second = history(), history(name="MED B")
    second["consumo"] *= 100
    features = FeatureEngineer().create_features(pd.concat([first, second]))
    a = features[features["medicamento"].eq("MED A")]
    assert a["lag_1"].iloc[1] == 100


def test_recursive_forecast_calendar_and_temporal_holdout():
    result = analyze(history(), months=3)
    assert list(result.predictions["data"]) == ["2025-01", "2025-02", "2025-03"]
    metrics = result.metrics.iloc[0]
    assert metrics["treino_ate"] < metrics["teste_de"]
    assert metrics["teste_ate"] == "2024-12"
    row = result.risks.iloc[0]
    assert row["necessidade_total"] == pytest.approx(row["consumo_previsto"] * 1.2)
    assert row["deficit"] == pytest.approx(max(0, row["necessidade_total"] - 400))


def test_latest_missing_stock_is_not_replaced_by_older_balance():
    raw = history()
    raw.loc[len(raw) - 1, "estoque_atual"] = np.nan
    result = analyze(raw)
    assert result.risks.iloc[0]["nivel_risco"] == "Sem dados"
    assert pd.isna(result.risks.iloc[0]["estoque_atual"])


@pytest.mark.parametrize(
    "mutation",
    ["duplicate", "missing_month", "negative", "invalid_date", "missing_consumption"],
)
def test_invalid_inputs_are_rejected(mutation):
    raw = history()
    if mutation == "duplicate":
        raw = pd.concat([raw, raw.iloc[[0]]])
    elif mutation == "missing_month":
        raw = raw.drop(4)
    elif mutation == "negative":
        raw.loc[0, "consumo"] = -1
    elif mutation == "invalid_date":
        raw.loc[0, "data"] = "2024-13"
    else:
        raw.loc[0, "consumo"] = np.nan
    with pytest.raises(ValueError):
        DataCleaner().clean(raw)


def test_insufficient_history_is_explicit():
    with pytest.raises(ValueError, match="Histórico insuficiente"):
        analyze(history(6))


def test_high_consumption_is_preserved():
    raw = history()
    raw.loc[10, "consumo"] = 1000000
    assert DataCleaner().clean(raw).loc[10, "consumo"] == 1000000
