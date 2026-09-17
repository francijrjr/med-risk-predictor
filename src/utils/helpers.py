"""Formatting helpers shared by the interface."""


def format_number(value: float, decimals: int = 2) -> str:
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")
