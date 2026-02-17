"""Currency and percentage formatting helpers."""

from __future__ import annotations


def format_currency(value: float, currency: str = "USD") -> str:
    """Format *value* as a currency string, e.g. ``$12,345.67``."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}
    symbol = symbols.get(currency, "$")
    if value < 0:
        return f"-{symbol}{abs(value):,.2f}"
    return f"{symbol}{value:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Convert a value (0-100 scale or 0-1 scale) to a display string."""
    if 0 < value < 1:
        value *= 100  # assume 0-1 scale
    return f"{value:.{decimals}f}%"
