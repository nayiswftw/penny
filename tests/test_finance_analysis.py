"""Unit tests for penny.finance_analysis — pure computation functions."""

from __future__ import annotations

import pandas as pd

from finance_analysis import (
    analyze_savings_rate,
    calculate_budget_breakdown,
    compute_debt_metrics,
    generate_summary_report,
    project_investment_growth,
    score_financial_health,
)

# ─── calculate_budget_breakdown ──────────────────────────────────────────────


class TestBudgetBreakdown:
    def test_normal_case(self, sample_income: float, sample_expenses: dict):
        result = calculate_budget_breakdown(sample_income, sample_expenses)
        assert result["total_expenses"] == sum(sample_expenses.values())
        assert result["surplus"] == sample_income - result["total_expenses"]
        assert isinstance(result["expense_ratios"], dict)
        assert "savings_potential" in result

    def test_zero_income(self, sample_expenses: dict):
        result = calculate_budget_breakdown(0, sample_expenses)
        assert result["savings_potential"] == 0.0
        assert all(v == 0.0 for v in result["expense_ratios"].values())

    def test_no_expenses(self, sample_income: float):
        result = calculate_budget_breakdown(sample_income, {})
        assert result["total_expenses"] == 0
        assert result["surplus"] == sample_income
        assert result["savings_potential"] == 100.0

    def test_expenses_exceed_income(self):
        result = calculate_budget_breakdown(1000, {"Rent": 1500})
        assert result["surplus"] == -500
        assert result["savings_potential"] < 0

    def test_surplus_formatted(self, sample_income: float, sample_expenses: dict):
        result = calculate_budget_breakdown(sample_income, sample_expenses)
        assert "$" in result["surplus_formatted"]


# ─── analyze_savings_rate ────────────────────────────────────────────────────


class TestSavingsRate:
    def test_excellent_rate(self):
        result = analyze_savings_rate(5000, 1500)
        assert result["rate"] == 30.0
        assert "Excellent" in result["status"]
        assert result["gap"] == 0

    def test_fair_rate(self):
        result = analyze_savings_rate(5000, 600)
        assert result["rate"] == 12.0
        assert "Fair" in result["status"]

    def test_low_rate(self):
        result = analyze_savings_rate(5000, 200)
        assert result["rate"] == 4.0
        assert "Low" in result["status"]

    def test_zero_income(self):
        result = analyze_savings_rate(0, 0)
        assert result["rate"] == 0.0
        assert "No income" in result["status"]

    def test_negative_savings(self):
        result = analyze_savings_rate(5000, -500)
        assert result["rate"] < 0


# ─── compute_debt_metrics ────────────────────────────────────────────────────


class TestDebtMetrics:
    def test_normal_debts(self, sample_debts: list, sample_income: float):
        result = compute_debt_metrics(sample_debts, sample_income)
        assert result["dti"] > 0
        assert result["total_balance"] == 30000.0
        assert len(result["debts_detail"]) == 2
        assert len(result["payoff_timeline"]) > 0

    def test_no_debts(self, sample_income: float):
        result = compute_debt_metrics([], sample_income)
        assert result["dti"] == 0.0
        assert result["total_balance"] == 0.0
        assert result["debts_detail"] == []
        assert result["payoff_timeline"] == []

    def test_zero_income_dti(self, sample_debts: list):
        result = compute_debt_metrics(sample_debts, 0)
        assert result["dti"] == 0.0

    def test_avalanche_ordering(self, sample_debts: list, sample_income: float):
        result = compute_debt_metrics(sample_debts, sample_income)
        rates = [d["interest_rate"] for d in result["debts_detail"]]
        assert rates == sorted(rates, reverse=True), "Debts should be ordered highest rate first"

    def test_single_debt(self, sample_income: float):
        debt = [{"name": "Car", "balance": 10000, "interest_rate": 4.0, "min_payment": 300}]
        result = compute_debt_metrics(debt, sample_income)
        assert len(result["debts_detail"]) == 1
        assert result["debts_detail"][0]["payoff_months"] > 0


# ─── project_investment_growth ───────────────────────────────────────────────


class TestInvestmentGrowth:
    def test_basic_growth(self):
        df = project_investment_growth(10000, 8.0, 10)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 11  # year 0 through 10
        assert df.iloc[-1]["total_value"] > 10000

    def test_with_contributions(self):
        df = project_investment_growth(0, 8.0, 10, 500)
        assert df.iloc[-1]["total_value"] > 0
        assert df.iloc[-1]["contributions"] == 500 * 12 * 10

    def test_zero_rate(self):
        df = project_investment_growth(10000, 0.0, 5)
        assert df.iloc[-1]["total_value"] == 10000
        assert df.iloc[-1]["returns"] == 0.0

    def test_single_year(self):
        df = project_investment_growth(10000, 10.0, 1)
        assert len(df) == 2  # year 0 + year 1
        assert df.iloc[-1]["total_value"] > 10000

    def test_columns_present(self):
        df = project_investment_growth(1000, 5.0, 3)
        for col in ["year", "total_value", "contributions", "returns"]:
            assert col in df.columns


# ─── score_financial_health ──────────────────────────────────────────────────


class TestHealthScore:
    def test_perfect_score(self):
        metrics = {"savings_rate": 25, "dti": 5, "savings_potential": 25, "has_investments": True}
        score = score_financial_health(metrics)
        assert score == 100

    def test_zero_score(self):
        metrics = {"savings_rate": 0, "dti": 50, "savings_potential": 0, "has_investments": False}
        score = score_financial_health(metrics)
        assert score == 0

    def test_moderate_score(self):
        metrics = {"savings_rate": 15, "dti": 20, "savings_potential": 15, "has_investments": True}
        score = score_financial_health(metrics)
        assert 40 <= score <= 80

    def test_clamped_0_to_100(self):
        score = score_financial_health({})
        assert 0 <= score <= 100

    def test_with_sample_metrics(self, sample_metrics: dict):
        score = score_financial_health(sample_metrics)
        assert 0 <= score <= 100


# ─── generate_summary_report ─────────────────────────────────────────────────


class TestSummaryReport:
    def test_keys_present(self, sample_income: float, sample_expenses: dict, sample_debts: list):
        budget = calculate_budget_breakdown(sample_income, sample_expenses)
        savings = analyze_savings_rate(sample_income, budget["surplus"])
        debt = compute_debt_metrics(sample_debts, sample_income)
        inv = project_investment_growth(10000, 8, 10, 200)
        health = score_financial_health({"savings_rate": savings["rate"], "dti": debt["dti"]})

        report = generate_summary_report(budget, savings, debt, inv, health)
        for key in ["monthly_income_surplus", "total_expenses", "savings_rate", "dti", "health_score"]:
            assert key in report

    def test_with_no_investments(self, sample_income: float, sample_expenses: dict):
        budget = calculate_budget_breakdown(sample_income, sample_expenses)
        savings = analyze_savings_rate(sample_income, budget["surplus"])
        debt = compute_debt_metrics([], sample_income)
        report = generate_summary_report(budget, savings, debt, None, 50)
        assert "projected_portfolio" not in report
