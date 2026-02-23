"""
dashboard.py — Dashboard Tab
─────────────────────────────
KPI metrics, interactive charts, summary table, and CSV export.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from penny.utils.export import export_to_csv
from penny.utils.formatting import format_currency
from penny.visualization import (
    render_budget_waterfall,
    render_debt_payoff_timeline,
    render_expense_pie_chart,
    render_financial_health_gauge,
    render_income_vs_expense_bar,
    render_investment_growth_line,
)


def render_dashboard(results: dict | None) -> None:
    """Render the Dashboard tab contents."""
    if results is None:
        st.info("Enter your financial data in the sidebar and click **Analyze My Finances** to get started.")
        return

    budget = results["budget"]
    savings = results["savings"]
    debt_met = results["debt"]
    inv_df = results["investment_df"]
    health = results["health_score"]
    _income = results["income"]
    _expenses = results["expenses"]

    # ── KPI Metrics ──────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            "Monthly Surplus",
            format_currency(budget["surplus"]),
            delta=f"{budget['savings_potential']:.1f}% of income",
        )
    with k2:
        st.metric(
            "Savings Rate",
            savings["rate_display"],
            delta=f"-{savings['gap']}% vs benchmark" if savings["gap"] > 0 else "On target",
            delta_color="inverse" if savings["gap"] > 0 else "normal",
        )
    with k3:
        st.metric(
            "Debt-to-Income",
            debt_met["dti_display"] if debt_met["dti"] > 0 else "0.0%",
            delta="Healthy" if debt_met["dti"] <= 15 else ("Moderate" if debt_met["dti"] <= 36 else "High"),
            delta_color="normal" if debt_met["dti"] <= 15 else ("off" if debt_met["dti"] <= 36 else "inverse"),
        )
    with k4:
        st.metric(
            "Health Score",
            f"{health}/100",
            delta="Excellent" if health >= 70 else ("Fair" if health >= 40 else "Needs Work"),
            delta_color="normal" if health >= 70 else ("off" if health >= 40 else "inverse"),
        )

    st.divider()

    # ── Chart Row 1 ──────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        non_zero_expenses = {k: v for k, v in _expenses.items() if v > 0}
        if non_zero_expenses:
            st.plotly_chart(render_expense_pie_chart(non_zero_expenses), width="stretch")
        else:
            st.info("No expense data to visualize.")
    with c2:
        st.plotly_chart(
            render_income_vs_expense_bar(_income, budget["total_expenses"]),
            width="stretch",
        )

    # ── Chart Row 2 — Investment Growth ──────────────────────────────
    st.plotly_chart(render_investment_growth_line(inv_df), width="stretch")

    # ── Chart Row 3 ──────────────────────────────────────────────────
    c3, c4 = st.columns(2)
    with c3:
        if debt_met["payoff_timeline"]:
            debt_names = [d["name"] for d in debt_met["debts_detail"]]
            st.plotly_chart(
                render_debt_payoff_timeline(debt_met["payoff_timeline"], debt_names),
                width="stretch",
            )
        else:
            st.success("No debts — you're debt-free!")
    with c4:
        st.plotly_chart(render_financial_health_gauge(health), width="stretch")

    # ── Waterfall ────────────────────────────────────────────────────
    non_zero_expenses = {k: v for k, v in _expenses.items() if v > 0}
    if non_zero_expenses:
        st.plotly_chart(render_budget_waterfall(_income, non_zero_expenses), width="stretch")

    # ── Summary Table + Export ───────────────────────────────────────
    with st.expander("Full Financial Summary"):
        report = results["report"]
        summary_data = {
            "Monthly Income": format_currency(_income),
            "Total Expenses": format_currency(budget["total_expenses"]),
            "Monthly Surplus": format_currency(budget["surplus"]),
            "Savings Rate": savings["rate_display"],
            "Savings Status": savings["status"],
            "Debt-to-Income": debt_met.get("dti_display", "0.0%"),
            "Total Debt": format_currency(debt_met["total_balance"]),
            "Health Score": f"{health}/100",
        }
        if report.get("projected_portfolio"):
            summary_data["Projected Portfolio"] = format_currency(report["projected_portfolio"])

        st.table(pd.DataFrame(list(summary_data.items()), columns=["Metric", "Value"]))

        csv = export_to_csv(summary_data)
        st.download_button(
            "Export to CSV",
            data=csv,
            file_name=f"financial_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
