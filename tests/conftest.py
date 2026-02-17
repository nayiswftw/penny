"""Shared test fixtures for the Penny test suite."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_income() -> float:
    return 5000.0


@pytest.fixture
def sample_expenses() -> dict[str, float]:
    return {
        "Housing": 1500.0,
        "Transportation": 400.0,
        "Food": 600.0,
        "Healthcare": 200.0,
        "Entertainment": 150.0,
        "Utilities": 250.0,
        "Insurance": 300.0,
    }


@pytest.fixture
def sample_debts() -> list[dict]:
    return [
        {"name": "Credit Card", "balance": 5000.0, "interest_rate": 18.0, "min_payment": 150.0},
        {"name": "Student Loan", "balance": 25000.0, "interest_rate": 5.5, "min_payment": 280.0},
    ]


@pytest.fixture
def sample_goals() -> list[dict]:
    return [
        {
            "name": "Emergency Fund",
            "target_amount": 15000.0,
            "target_date": "2027-01-01",
            "priority": "High",
            "current_savings": 3000.0,
        },
        {
            "name": "Vacation",
            "target_amount": 5000.0,
            "target_date": "2026-12-01",
            "priority": "Low",
            "current_savings": 1500.0,
        },
    ]


@pytest.fixture
def sample_metrics(sample_income: float, sample_expenses: dict) -> dict:
    """Full metrics dict as produced by generate_summary_report."""
    total_exp = sum(sample_expenses.values())
    surplus = sample_income - total_exp
    return {
        "monthly_income_surplus": surplus,
        "total_expenses": total_exp,
        "expense_ratios": {k: round(v / sample_income * 100, 1) for k, v in sample_expenses.items()},
        "savings_rate": round(surplus / sample_income * 100, 1) if sample_income > 0 else 0,
        "savings_status": "✅ Excellent",
        "dti": 8.6,
        "total_debt": 30000.0,
        "health_score": 72,
        "has_investments": True,
        "savings_potential": round(surplus / sample_income * 100, 1),
    }
