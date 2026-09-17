"""Explicit source loading. Demo data must never impersonate DATASUS data."""

from pathlib import Path

import pandas as pd


class DataLoader:
    def __init__(self, data_dir="data/samples"):
        self.data_dir = Path(data_dir)

    def load_data(self, source="local"):
        if source != "local":
            raise ValueError(
                "A integração DATASUS não está implementada. Selecione um CSV ou a demonstração local."
            )
        return pd.read_csv(self.data_dir / "datasus_sample.csv")
