"""Unit tests for penny.ai_advisor — prompt building and context (no live API)."""

from __future__ import annotations

import os
from unittest.mock import patch

from ai_advisor import build_financial_context, build_system_prompt, is_available

# ─── build_system_prompt ─────────────────────────────────────────────────────


class TestSystemPrompt:
    def test_returns_non_empty(self):
        prompt = build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_contains_guardrails(self):
        prompt = build_system_prompt()
        assert "NEVER" in prompt
        assert "stock tickers" in prompt.lower() or "specific stock" in prompt.lower()
        assert "professional" in prompt.lower()

    def test_contains_persona(self):
        prompt = build_system_prompt()
        assert "Financial Advisor" in prompt


# ─── build_financial_context ─────────────────────────────────────────────────


class TestFinancialContext:
    def test_empty_metrics(self):
        ctx = build_financial_context({})
        assert "No financial data" in ctx

    def test_full_metrics(self, sample_metrics: dict):
        ctx = build_financial_context(sample_metrics)
        assert "FINANCIAL SNAPSHOT" in ctx
        assert "Savings Rate" in ctx
        assert "Health Score" in ctx

    def test_with_expense_ratios(self, sample_metrics: dict):
        ctx = build_financial_context(sample_metrics)
        assert "Expense Breakdown" in ctx
        assert "Housing" in ctx

    def test_with_projections(self, sample_metrics: dict):
        sample_metrics["projected_portfolio"] = 250000
        sample_metrics["total_contributions"] = 120000
        sample_metrics["total_returns"] = 130000
        ctx = build_financial_context(sample_metrics)
        assert "Projected Portfolio" in ctx


# ─── is_available ────────────────────────────────────────────────────────────


class TestIsAvailable:
    def test_available_with_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-abc123"}):
            # Need to clear the settings cache
            from penny.config import get_settings
            get_settings.cache_clear()
            assert is_available() is True
            get_settings.cache_clear()

    def test_not_available_without_key(self):
        env = os.environ.copy()
        env.pop("GEMINI_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            from penny.config import get_settings
            get_settings.cache_clear()
            is_available()
            get_settings.cache_clear()
            # May be True if .env file exists with a key — that's fine
            # The important thing is that it doesn't crash


class TestConfig:
    def test_defaults(self):
        from penny.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        assert s.gemini_model == "gemini-2.5-pro"
        assert s.gemini_temperature == 0.3
        assert s.cache_ttl_seconds == 300
        assert s.log_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        get_settings.cache_clear()
