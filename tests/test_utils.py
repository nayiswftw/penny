"""Unit tests for penny.utils sub-modules."""

from __future__ import annotations

import os
import tempfile
import time

from penny.utils.cache import cache_with_ttl
from penny.utils.export import export_to_csv
from penny.utils.formatting import format_currency, format_percentage
from penny.utils.sanitize import sanitize_user_input
from penny.utils.validation import validate_financial_inputs

# ─── format_currency ─────────────────────────────────────────────────────────


class TestFormatCurrency:
    def test_usd_default(self):
        assert format_currency(12345.67) == "$12,345.67"

    def test_eur(self):
        assert format_currency(1000, "EUR") == "€1,000.00"

    def test_gbp(self):
        assert format_currency(500, "GBP") == "£500.00"

    def test_inr(self):
        assert format_currency(100, "INR") == "₹100.00"

    def test_negative(self):
        result = format_currency(-250.50)
        assert result == "-$250.50"

    def test_zero(self):
        assert format_currency(0) == "$0.00"

    def test_unknown_currency(self):
        result = format_currency(100, "XYZ")
        assert "$" in result  # fallback to $


# ─── format_percentage ───────────────────────────────────────────────────────


class TestFormatPercentage:
    def test_normal(self):
        assert format_percentage(25.5) == "25.5%"

    def test_zero(self):
        assert format_percentage(0) == "0.0%"

    def test_fractional_input(self):
        """Values between 0 and 1 are auto-scaled to percentage."""
        assert format_percentage(0.5) == "50.0%"

    def test_custom_decimals(self):
        assert format_percentage(33.333, decimals=2) == "33.33%"


# ─── validate_financial_inputs ───────────────────────────────────────────────


class TestValidation:
    def test_valid_data(self, sample_income: float, sample_expenses: dict):
        errors = validate_financial_inputs({"income": sample_income, "expenses": sample_expenses})
        assert errors == []

    def test_missing_income(self, sample_expenses: dict):
        errors = validate_financial_inputs({"expenses": sample_expenses})
        assert any("income" in e.lower() for e in errors)

    def test_negative_income(self, sample_expenses: dict):
        errors = validate_financial_inputs({"income": -100, "expenses": sample_expenses})
        assert any("negative" in e.lower() for e in errors)

    def test_negative_expense(self):
        errors = validate_financial_inputs({"income": 5000, "expenses": {"Food": -50}})
        assert any("negative" in e.lower() for e in errors)

    def test_zero_expenses(self):
        errors = validate_financial_inputs({"income": 5000, "expenses": {"Food": 0}})
        assert any("greater than zero" in e.lower() for e in errors)

    def test_invalid_debt_rate(self):
        data = {"income": 5000, "expenses": {"Food": 100}, "debts": [{"name": "Bad", "interest_rate": 50}]}
        errors = validate_financial_inputs(data)
        assert any("interest rate" in e.lower() for e in errors)


# ─── export_to_csv ───────────────────────────────────────────────────────────


class TestExport:
    def test_dict_export(self):
        csv = export_to_csv({"Income": 5000, "Expenses": 3000})
        assert "Metric" in csv
        assert "5000" in csv

    def test_list_export(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        csv = export_to_csv(data)
        assert "a" in csv
        assert "3" in csv

    def test_empty_list(self):
        assert export_to_csv([]) == ""

    def test_write_to_file(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            export_to_csv({"X": 42}, filename=path)
            assert os.path.exists(path)
            with open(path) as f:
                assert "42" in f.read()
        finally:
            os.unlink(path)


# ─── sanitize_user_input ─────────────────────────────────────────────────────


class TestSanitize:
    def test_strips_whitespace(self):
        assert sanitize_user_input("  hello  ") == "hello"

    def test_removes_html_chars(self):
        result = sanitize_user_input("<script>alert('xss')</script>")
        assert "<" not in result
        assert ">" not in result

    def test_removes_braces(self):
        result = sanitize_user_input("test {injection}")
        assert "{" not in result
        assert "}" not in result

    def test_truncation(self):
        long_text = "a" * 5000
        result = sanitize_user_input(long_text)
        assert len(result) == 2000


# ─── cache_with_ttl ──────────────────────────────────────────────────────────


class TestCache:
    def test_caches_result(self):
        call_count = 0

        @cache_with_ttl(ttl=10)
        def compute(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert compute(5) == 10
        assert compute(5) == 10  # cached
        assert call_count == 1

    def test_different_args_not_cached(self):
        call_count = 0

        @cache_with_ttl(ttl=10)
        def compute(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        compute(1)
        compute(2)
        assert call_count == 2

    def test_expiry(self):
        call_count = 0

        @cache_with_ttl(ttl=1)
        def compute(x):
            nonlocal call_count
            call_count += 1
            return x

        compute(1)
        time.sleep(1.1)
        compute(1)  # should re-compute
        assert call_count == 2
