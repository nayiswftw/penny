"""
utils.py — Shared Utility Functions
────────────────────────────────────
Formatting, validation, caching, export, and logging helpers
used across all application modules.
"""

import csv
import io
import os
import re
import time
import logging
import functools
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


def get_secret(key: str, default: str = "") -> str:
    """Retrieve a config value from env vars or Streamlit Cloud secrets.

    Lookup order:
    1. ``os.environ`` (set by ``.env`` or the host environment)
    2. ``st.secrets``  (Streamlit Community Cloud)
    3. *default*
    """
    value = os.getenv(key)
    if value is not None:
        return value

    try:
        import streamlit as st  # noqa: delayed import to avoid issues outside Streamlit
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass

    return default


# ─── Logging ──────────────────────────────────────────────────────────────────

LOG_LEVEL = get_secret("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("penny")


# ─── Environment ──────────────────────────────────────────────────────────────

def load_env_config() -> dict:
    """Load and validate all required environment variables.

    Returns a dict of config values. Raises ``EnvironmentError`` if the
    mandatory ``GEMINI_API_KEY`` is missing or set to the placeholder.
    """
    config = {
        "GEMINI_API_KEY": get_secret("GEMINI_API_KEY"),
        "GEMINI_MODEL": get_secret("GEMINI_MODEL", "gemini-1.5-pro"),
        "GEMINI_MAX_TOKENS": int(get_secret("GEMINI_MAX_TOKENS", "8192")),
        "GEMINI_TEMPERATURE": float(get_secret("GEMINI_TEMPERATURE", "0.3")),
        "APP_TITLE": get_secret("APP_TITLE", "AI Financial Advisor"),
        "APP_ENV": get_secret("APP_ENV", "development"),
        "CACHE_TTL_SECONDS": int(get_secret("CACHE_TTL_SECONDS", "300")),
    }

    if not config["GEMINI_API_KEY"] or config["GEMINI_API_KEY"] == "your_google_gemini_api_key_here":
        logger.warning("GEMINI_API_KEY is missing — AI features will be disabled.")

    return config


# ─── Formatting ───────────────────────────────────────────────────────────────

def format_currency(value: float, currency: str = "USD") -> str:
    """Format *value* as a currency string, e.g. ``$12,345.67``."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}
    symbol = symbols.get(currency, "$")
    if value < 0:
        return f"-{symbol}{abs(value):,.2f}"
    return f"{symbol}{value:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Convert a value (0–100 scale or 0–1 scale) to a display string."""
    if 0 < value < 1:
        value *= 100  # assume 0-1 scale
    return f"{value:.{decimals}f}%"


# ─── Validation ───────────────────────────────────────────────────────────────

def validate_financial_inputs(data: dict) -> list[str]:
    """Validate user-supplied financial data.

    Returns a list of human-readable error messages (empty if valid).
    """
    errors: list[str] = []

    income = data.get("income")
    if income is None:
        errors.append("Monthly income is required.")
    elif not isinstance(income, (int, float)):
        errors.append("Income must be a number.")
    elif income < 0:
        errors.append("Income cannot be negative.")

    expenses = data.get("expenses", {})
    if not expenses or all(v == 0 for v in expenses.values()):
        errors.append("At least one expense category must have a value greater than zero.")
    for cat, val in expenses.items():
        if not isinstance(val, (int, float)):
            errors.append(f"Expense '{cat}' must be a number.")
        elif val < 0:
            errors.append(f"Expense '{cat}' cannot be negative.")

    for debt in data.get("debts", []):
        rate = debt.get("interest_rate", 0)
        if rate < 0.1 or rate > 30:
            errors.append(
                f"Interest rate {rate}% for '{debt.get('name', 'debt')}' "
                "should be between 0.1% and 30%."
            )

    return errors


# ─── Caching ──────────────────────────────────────────────────────────────────

def cache_with_ttl(ttl: int = 300):
    """Decorator that caches function results for *ttl* seconds."""

    def decorator(func):
        cache: dict = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in cache:
                result, ts = cache[key]
                if now - ts < ttl:
                    return result
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        wrapper.cache_clear = cache.clear
        return wrapper

    return decorator


# ─── Sanitization ─────────────────────────────────────────────────────────────

def sanitize_user_input(text: str) -> str:
    """Strip potentially harmful characters from user text."""
    text = text.strip()
    text = re.sub(r"[<>{}]", "", text)
    # Limit length to prevent prompt-injection-style payloads
    return text[:2000]


# ─── Financial Helpers ────────────────────────────────────────────────────────

def calculate_inflation_adjusted(value: float, rate: float, years: int) -> float:
    """Project *value* to its future inflation-adjusted equivalent.

    Parameters
    ----------
    rate : float
        Annual inflation rate as a percentage (e.g. 3.0 for 3%).
    """
    return value * ((1 + rate / 100) ** years)


# ─── Export ───────────────────────────────────────────────────────────────────

def export_to_csv(data_dict: dict, filename: str | None = None) -> str:
    """Serialize a flat dict (or list-of-dicts) to CSV text.

    Returns the CSV content as a string. If *filename* is provided the
    content is also written to disk.
    """
    buf = io.StringIO()

    if isinstance(data_dict, list):
        if not data_dict:
            return ""
        writer = csv.DictWriter(buf, fieldnames=data_dict[0].keys())
        writer.writeheader()
        writer.writerows(data_dict)
    else:
        writer = csv.writer(buf)
        writer.writerow(["Metric", "Value"])
        for k, v in data_dict.items():
            writer.writerow([k, v])

    content = buf.getvalue()

    if filename:
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, "w", newline="", encoding="utf-8") as f:
            f.write(content)

    return content


# ─── API Logging ──────────────────────────────────────────────────────────────

def log_api_usage(tokens_in: int, tokens_out: int, latency_ms: float) -> None:
    """Log Gemini API interaction metrics."""
    logger.info(
        "Gemini API  │  tokens_in=%d  tokens_out=%d  latency=%dms",
        tokens_in,
        tokens_out,
        int(latency_ms),
    )
