"""
sidebar.py — Sidebar Data Entry
────────────────────────────────
Collects income, expenses, debts, investments, and risk profile
from the user via Streamlit sidebar widgets.
"""

from __future__ import annotations

import streamlit as st


def render_sidebar() -> tuple[float, dict[str, float], float, float, float, int, str, bool]:
    """Render the sidebar and return collected user inputs.

    Returns
    -------
    tuple of:
        income, expenses, portfolio_value, monthly_contribution,
        annual_return, time_horizon, risk_profile, analyze_clicked
    """
    with st.sidebar:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
                <i class="lucide-sliders-horizontal" style="color:#818cf8;font-size:16px"></i>
                <span style="font-size:15px;font-weight:700;color:#f0f0f5;letter-spacing:-0.3px">Financial Data</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Income ────────────────────────────────────────────────────────
        st.markdown(
            '<p class="section-label"><i class="lucide-banknote" style="font-size:12px;margin-right:4px"></i> Income</p>',
            unsafe_allow_html=True,
        )
        income = st.number_input("Monthly Gross Income ($)", min_value=0.0, value=0.0, step=100.0, key="income_input")
        income_freq = st.selectbox("Income Frequency", ["Monthly", "Annually"], key="income_freq")
        if income_freq == "Annually":
            income = income / 12
        st.text_area("Additional Income Sources (optional)", key="add_income", height=68)

        st.divider()

        # ── Expenses ──────────────────────────────────────────────────────
        st.markdown(
            '<p class="section-label"><i class="lucide-receipt" style="font-size:12px;margin-right:4px"></i> Monthly Expenses</p>',
            unsafe_allow_html=True,
        )
        expense_categories = ["Housing", "Transportation", "Food", "Healthcare", "Entertainment", "Utilities", "Insurance"]
        expenses: dict[str, float] = {}
        for cat in expense_categories:
            expenses[cat] = st.number_input(f"{cat} ($)", min_value=0.0, value=0.0, step=50.0, key=f"exp_{cat}")

        st.divider()

        # ── Debts ─────────────────────────────────────────────────────────
        st.markdown(
            '<p class="section-label"><i class="lucide-credit-card" style="font-size:12px;margin-right:4px"></i> Debts</p>',
            unsafe_allow_html=True,
        )
        debt_types = ["Credit Card", "Student Loan", "Mortgage", "Auto Loan", "Personal Loan", "Other"]

        if "debt_count" not in st.session_state:
            st.session_state.debt_count = 0

        for i in range(st.session_state.debt_count):
            with st.expander(f"Debt #{i + 1}", expanded=True):
                st.selectbox("Type", debt_types, key=f"debt_type_{i}")
                st.number_input("Balance ($)", min_value=0.0, value=0.0, step=100.0, key=f"debt_bal_{i}")
                st.number_input("Interest Rate (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5, key=f"debt_rate_{i}")
                st.number_input("Min. Monthly Payment ($)", min_value=0.0, value=0.0, step=25.0, key=f"debt_pay_{i}")

        if st.button("Add Debt", key="add_debt_btn"):
            st.session_state.debt_count += 1
            st.rerun()

        st.divider()

        # ── Investments ───────────────────────────────────────────────────
        st.markdown(
            '<p class="section-label"><i class="lucide-trending-up" style="font-size:12px;margin-right:4px"></i> Investments</p>',
            unsafe_allow_html=True,
        )
        portfolio_value = st.number_input("Current Portfolio Value ($)", min_value=0.0, value=0.0, step=500.0, key="portfolio")
        monthly_contribution = st.number_input("Monthly Contribution ($)", min_value=0.0, value=0.0, step=50.0, key="monthly_contrib")
        annual_return = st.slider("Expected Annual Return (%)", min_value=1.0, max_value=15.0, value=8.0, step=0.5, key="annual_return")
        time_horizon = st.slider("Time Horizon (years)", min_value=1, max_value=40, value=20, key="time_horizon")

        st.divider()

        # ── Risk Profile ──────────────────────────────────────────────────
        st.markdown(
            '<p class="section-label"><i class="lucide-shield" style="font-size:12px;margin-right:4px"></i> Risk Profile</p>',
            unsafe_allow_html=True,
        )
        risk_profile = st.radio("Investment Risk Tolerance", ["Conservative", "Moderate", "Aggressive"], index=1, key="risk_profile")

        st.divider()

        # ── Analyze Button ────────────────────────────────────────────────
        analyze_clicked = st.button("Analyze My Finances", type="primary", width="stretch")

    return income, expenses, portfolio_value, monthly_contribution, annual_return, time_horizon, risk_profile, analyze_clicked
