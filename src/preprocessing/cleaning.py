"""Validate monthly snapshots without silently inventing or discarding values."""

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["medicamento", "data", "consumo", "estoque_atual"]
SERIES_COLUMNS = ["unidade", "medicamento"]


class DataCleaner:
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            raise ValueError("O arquivo não contém registros.")
        missing = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(sorted(missing)))
        result = df.copy()
        if "unidade" not in result:
            result["unidade"] = "Unidade não informada"
        for column in SERIES_COLUMNS:
            if result[column].isna().any():
                raise ValueError(f"Preencha todos os valores de {column}.")
            result[column] = result[column].astype(str).str.strip()
            if result[column].eq("").any():
                raise ValueError(f"Valores vazios em {column}.")
        result["medicamento"] = result["medicamento"].str.upper()
        if not result["data"].astype(str).str.fullmatch(r"\d{4}-\d{2}").all():
            raise ValueError("Use datas mensais no formato YYYY-MM.")
        dates = pd.to_datetime(result["data"], format="%Y-%m", errors="coerce")
        if dates.isna().any():
            raise ValueError("Existem meses ou anos inválidos no arquivo.")
        for column in ("consumo", "estoque_atual"):
            original = result[column]
            values = pd.to_numeric(original, errors="coerce")
            invalid = (
                (original.notna() & values.isna())
                | (values.notna() & ~np.isfinite(values))
                | values.lt(0)
            )
            if invalid.any() or (column == "consumo" and values.isna().any()):
                raise ValueError(
                    f"{column}: use números não negativos; consumo não pode estar vazio."
                )
            result[column] = values
        if result.duplicated(SERIES_COLUMNS + ["data"]).any():
            raise ValueError(
                "Há mais de um registro por unidade, medicamento e mês. Consolide o consumo e informe o saldo final antes de importar."
            )
        result = result.sort_values(SERIES_COLUMNS + ["data"]).reset_index(drop=True)
        for key, group in result.groupby(SERIES_COLUMNS):
            expected = pd.period_range(group["data"].min(), group["data"].max(), freq="M")
            if len(expected) != len(group):
                raise ValueError(
                    f"Há meses ausentes na série {key[0]} / {key[1]}. Corrija o histórico; ausência não significa consumo zero."
                )
        return result
