"""
finance_analysis.py — Financial Computation Engine
───────────────────────────────────────────────────
Budget breakdowns, savings analysis, debt metrics,
investment projections, and composite health scoring.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from utils import format_currency, format_percentage


# ─── Budget ───────────────────────────────────────────────────────────────────

def calculate_budget_breakdown(income: float, expenses: dict[str, float]) -> dict:
    """Compute discretionary income, savings potential, and per-category ratios.

    Parameters
    ----------
    income : float
        Monthly gross income.
    expenses : dict
        Mapping of category name → monthly amount.

    Returns
    -------
    dict with keys: total_expenses, surplus, expense_ratios, savings_potential.
    """
    total_expenses = sum(expenses.values())
    surplus = income - total_expenses

    if income > 0:
        expense_ratios = {cat: round(val / income * 100, 1) for cat, val in expenses.items()}
        savings_potential = round(surplus / income * 100, 1)
    else:
        expense_ratios = {cat: 0.0 for cat in expenses}
        savings_potential = 0.0

    return {
        "total_expenses": total_expenses,
        "surplus": surplus,
        "expense_ratios": expense_ratios,
        "savings_potential": savings_potential,
        "surplus_formatted": format_currency(surplus),
    }


# ─── Savings ──────────────────────────────────────────────────────────────────

def analyze_savings_rate(income: float, savings: float) -> dict:
    """Return savings-rate metrics and benchmark against the 20 % rule.

    Parameters
    ----------
    income : float
        Monthly gross income.
    savings : float
        Monthly savings amount (surplus directed to savings).
    """
    if income <= 0:
        return {"rate": 0.0, "status": "⚠️ No income reported", "gap": 0.0, "rate_display": "0.0%"}

    rate = savings / income * 100
    benchmark = 20.0
    gap = benchmark - rate

    if rate >= benchmark:
        status = "✅ Excellent — meets or exceeds the 20% savings rule"
    elif rate >= 10:
        status = "⚠️ Fair — below the recommended 20% benchmark"
    else:
        status = "❌ Low — significantly below recommended savings rate"

    return {
        "rate": round(rate, 1),
        "status": status,
        "gap": round(max(gap, 0), 1),
        "rate_display": format_percentage(rate),
    }


# ─── Debt ─────────────────────────────────────────────────────────────────────

def _payoff_months(balance: float, rate_annual: float, payment: float) -> int:
    """Estimate months to pay off a single debt at *payment* per month."""
    if payment <= 0 or balance <= 0:
        return 0
    r = rate_annual / 100 / 12
    if r == 0:
        return math.ceil(balance / payment)
    # Prevent log of non-positive
    denom = payment - balance * r
    if denom <= 0:
        return 999  # effectively never paid off at this rate
    months = math.ceil(-math.log(1 - balance * r / payment) / math.log(1 + r))
    return min(months, 999)


def compute_debt_metrics(debts: list[dict], income: float) -> dict:
    """Calculate DTI ratio, total burden, and payoff timelines.

    Each debt dict must contain: name, balance, interest_rate, min_payment.

    Returns
    -------
    dict with keys: dti, total_balance, total_min_payment,
                    debts_detail (list), payoff_timeline.
    """
    if not debts:
        return {
            "dti": 0.0,
            "total_balance": 0.0,
            "total_min_payment": 0.0,
            "debts_detail": [],
            "payoff_timeline": [],
        }

    total_balance = sum(d.get("balance", 0) for d in debts)
    total_min_payment = sum(d.get("min_payment", 0) for d in debts)
    dti = (total_min_payment / income * 100) if income > 0 else 0.0

    details = []
    # Sort by interest rate descending (avalanche order)
    sorted_debts = sorted(debts, key=lambda d: d.get("interest_rate", 0), reverse=True)
    for d in sorted_debts:
        months = _payoff_months(d["balance"], d["interest_rate"], d["min_payment"])
        details.append({
            "name": d.get("name", "Debt"),
            "balance": d["balance"],
            "interest_rate": d["interest_rate"],
            "min_payment": d["min_payment"],
            "payoff_months": months,
        })

    # Build a monthly timeline for chart consumption
    timeline: list[dict] = []
    sim_debts = [
        {"name": d["name"], "balance": float(d["balance"]),
         "rate_m": d["interest_rate"] / 100 / 12, "payment": float(d["min_payment"])}
        for d in sorted_debts
    ]
    for month in range(1, 361):  # up to 30 years
        row: dict[str, Any] = {"month": month}
        all_zero = True
        for sd in sim_debts:
            interest = sd["balance"] * sd["rate_m"]
            sd["balance"] = max(sd["balance"] + interest - sd["payment"], 0)
            row[sd["name"]] = round(sd["balance"], 2)
            if sd["balance"] > 0:
                all_zero = False
        timeline.append(row)
        if all_zero:
            break

    return {
        "dti": round(dti, 1),
        "dti_display": format_percentage(dti),
        "total_balance": total_balance,
        "total_min_payment": total_min_payment,
        "debts_detail": details,
        "payoff_timeline": timeline,
    }


# ─── Investment Projection ────────────────────────────────────────────────────

def project_investment_growth(
    principal: float,
    annual_rate: float,
    years: int,
    monthly_contribution: float = 0.0,
) -> pd.DataFrame:
    """Compound-interest growth projection.

    Parameters
    ----------
    principal : float
        Starting investment value.
    annual_rate : float
        Expected annual return as a percentage (e.g. 8 for 8 %).
    years : int
        Investment time horizon in years.
    monthly_contribution : float
        Additional amount invested each month.

    Returns
    -------
    pd.DataFrame with columns: year, total_value, contributions, returns.
    """
    r_monthly = annual_rate / 100 / 12
    records = [{"year": 0, "total_value": principal, "contributions": principal, "returns": 0.0}]

    balance = principal
    total_contributed = principal

    for y in range(1, years + 1):
        for _ in range(12):
            balance = balance * (1 + r_monthly) + monthly_contribution
            total_contributed += monthly_contribution
        records.append({
            "year": y,
            "total_value": round(balance, 2),
            "contributions": round(total_contributed, 2),
            "returns": round(balance - total_contributed, 2),
        })

    return pd.DataFrame(records)


# ─── Health Score ─────────────────────────────────────────────────────────────

def score_financial_health(metrics: dict) -> int:
    """Generate a composite Financial Health Score from 0 to 100.

    Weighted breakdown
    ------------------
    - Savings rate   : 30 %
    - Debt-to-income : 25 %
    - Budget surplus : 25 %
    - Investment     : 20 %
    """
    score = 0.0

    # Savings rate component (target ≥ 20%)
    savings_rate = metrics.get("savings_rate", 0)
    score += min(savings_rate / 20, 1) * 30

    # DTI component (lower is better, target ≤ 15%)
    dti = metrics.get("dti", 0)
    if dti <= 15:
        score += 25
    elif dti <= 36:
        score += 25 * (1 - (dti - 15) / 21)
    # else: 0

    # Budget surplus component (target ≥ 20% of income)
    surplus_pct = metrics.get("savings_potential", 0)
    score += min(surplus_pct / 20, 1) * 25

    # Investment component — has any investing activity
    has_investments = metrics.get("has_investments", False)
    if has_investments:
        score += 20

    return max(0, min(100, int(round(score))))


# ─── Summary Report ──────────────────────────────────────────────────────────

def generate_summary_report(
    budget: dict,
    savings: dict,
    debt: dict,
    investment_df: pd.DataFrame | None,
    health_score: int,
) -> dict:
    """Produce a structured dictionary consumed by the AI advisor and viz layer."""
    report: dict[str, Any] = {
        "monthly_income_surplus": budget.get("surplus", 0),
        "total_expenses": budget.get("total_expenses", 0),
        "expense_ratios": budget.get("expense_ratios", {}),
        "savings_rate": savings.get("rate", 0),
        "savings_status": savings.get("status", ""),
        "dti": debt.get("dti", 0),
        "total_debt": debt.get("total_balance", 0),
        "health_score": health_score,
    }

    if investment_df is not None and not investment_df.empty:
        final = investment_df.iloc[-1]
        report["projected_portfolio"] = final["total_value"]
        report["total_contributions"] = final["contributions"]
        report["total_returns"] = final["returns"]

    return report
