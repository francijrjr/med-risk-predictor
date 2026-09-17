"""TCC rule: (forecast demand + safety stock) / available stock.

Thresholds are illustrative, not calibrated against municipal shortages.
"""

import numpy as np
import pandas as pd

RISK_ORDER = {"Alto": 0, "Médio": 1, "Sem dados": 2, "Baixo": 3}
RISK_COLORS = {
    "Alto": "#b83e35",
    "Médio": "#aa701b",
    "Baixo": "#227767",
    "Sem dados": "#6b7280",
}


class RiskClassifier:
    def __init__(self, safety_percentage: float = 0.2):
        if not 0 <= safety_percentage <= 1:
            raise ValueError("A reserva de segurança deve estar entre 0% e 100%.")
        self.safety_percentage = safety_percentage

    def classify_risk(self, estoque: float, previsao: float) -> str:
        if pd.isna(estoque) or pd.isna(previsao):
            return "Sem dados"
        if estoque < 0 or previsao < 0:
            raise ValueError("Estoque e previsão não podem ser negativos.")
        if estoque == 0:
            return "Alto" if previsao > 0 else "Sem dados"
        index = previsao * (1 + self.safety_percentage) / estoque
        if index > 1.3:
            return "Alto"
        return "Médio" if index >= 1 else "Baixo"

    def classify_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        result["estoque_seguranca"] = result["consumo_previsto"] * self.safety_percentage
        result["necessidade_total"] = result["consumo_previsto"] + result["estoque_seguranca"]
        result["indice_risco"] = result["necessidade_total"] / result["estoque_atual"].replace(
            0, np.nan
        )
        result.loc[
            result["estoque_atual"].eq(0) & result["necessidade_total"].gt(0),
            "indice_risco",
        ] = np.inf
        result["deficit"] = (result["necessidade_total"] - result["estoque_atual"]).clip(lower=0)
        result["nivel_risco"] = [
            self.classify_risk(s, p)
            for s, p in zip(result["estoque_atual"], result["consumo_previsto"])
        ]
        result["acao_sugerida"] = result["nivel_risco"].map(
            {
                "Alto": "Priorizar avaliação de reposição ou redistribuição",
                "Médio": "Revisar prazo de reposição e acompanhar estoque",
                "Baixo": "Manter acompanhamento do consumo",
                "Sem dados": "Conferir saldo e histórico antes de decidir",
            }
        )
        return result.sort_values("nivel_risco", key=lambda levels: levels.map(RISK_ORDER))
