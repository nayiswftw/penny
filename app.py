"""
app.py — Penny: AI Financial Advisor (Streamlit)
─────────────────────────────────────────────────
Main application entry point.  Three tabs:
  1. Dashboard  — KPI metrics + interactive charts
  2. AI Advisor — Gemini-powered chat with financial context
  3. Goals      — Goal tracking, feasibility, AI plans, retirement calc
"""

from __future__ import annotations

import os
import math
from datetime import datetime, date

import streamlit as st
import pandas as pd

from utils import (
    load_env_config,
    format_currency,
    format_percentage,
    validate_financial_inputs,
    export_to_csv,
)
from finance_analysis import (
    calculate_budget_breakdown,
    analyze_savings_rate,
    compute_debt_metrics,
    project_investment_growth,
    score_financial_health,
    generate_summary_report,
)
from visualization import (
    render_expense_pie_chart,
    render_income_vs_expense_bar,
    render_investment_growth_line,
    render_debt_payoff_timeline,
    render_financial_health_gauge,
    render_savings_progress_bar,
    render_budget_waterfall,
)
import ai_advisor

# ══════════════════════════════════════════════════════════════════════════════
# Page Config  (MUST be the first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Penny — AI Financial Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lucide Icons CDN ──────────────────────────────────────────────────────────
st.markdown(
    "<style>@import url('https://unpkg.com/lucide-static@latest/font/lucide.css');</style>",
    unsafe_allow_html=True,
)

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    "chat_history": [],
    "financial_data": {},
    "analysis_results": None,
    "goals": [],
    "debts": [],
}
for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ══════════════════════════════════════════════════════════════════════════════
# Header
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(
    """
    <div class="app-header">
        <div class="logo-icon"><i class="lucide-wallet"></i></div>
        <div>
            <h1>Penny</h1>
            <p>AI-powered financial analysis, planning &amp; advice</p>
        </div>
        <div class="header-badge"><i class="lucide-activity" style="font-size:10px;margin-right:4px"></i> Live</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# Sidebar — Data Entry (revamped)
# ══════════════════════════════════════════════════════════════════════════════

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

    # ── Income ────────────────────────────────────────────────────────────
    st.markdown('<p class="section-label"><i class="lucide-banknote" style="font-size:12px;margin-right:4px"></i> Income</p>', unsafe_allow_html=True)
    income = st.number_input("Monthly Gross Income ($)", min_value=0.0, value=0.0, step=100.0, key="income_input")
    income_freq = st.selectbox("Income Frequency", ["Monthly", "Annually"], key="income_freq")
    if income_freq == "Annually":
        income = income / 12
    additional_income = st.text_area("Additional Income Sources (optional)", key="add_income", height=68)

    st.divider()

    # ── Expenses ──────────────────────────────────────────────────────────
    st.markdown('<p class="section-label"><i class="lucide-receipt" style="font-size:12px;margin-right:4px"></i> Monthly Expenses</p>', unsafe_allow_html=True)
    expense_categories = ["Housing", "Transportation", "Food", "Healthcare", "Entertainment", "Utilities", "Insurance"]
    expenses: dict[str, float] = {}
    for cat in expense_categories:
        expenses[cat] = st.number_input(f"{cat} ($)", min_value=0.0, value=0.0, step=50.0, key=f"exp_{cat}")

    st.divider()

    # ── Debts ─────────────────────────────────────────────────────────────
    st.markdown('<p class="section-label"><i class="lucide-credit-card" style="font-size:12px;margin-right:4px"></i> Debts</p>', unsafe_allow_html=True)
    debt_types = ["Credit Card", "Student Loan", "Mortgage", "Auto Loan", "Personal Loan", "Other"]

    if "debt_count" not in st.session_state:
        st.session_state.debt_count = 0

    for i in range(st.session_state.debt_count):
        with st.expander(f"Debt #{i+1}", expanded=True):
            d_name = st.selectbox("Type", debt_types, key=f"debt_type_{i}")
            d_balance = st.number_input("Balance ($)", min_value=0.0, value=0.0, step=100.0, key=f"debt_bal_{i}")
            d_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5, key=f"debt_rate_{i}")
            d_payment = st.number_input("Min. Monthly Payment ($)", min_value=0.0, value=0.0, step=25.0, key=f"debt_pay_{i}")

    if st.button("Add Debt", key="add_debt_btn"):
        st.session_state.debt_count += 1
        st.rerun()

    st.divider()

    # ── Investments ───────────────────────────────────────────────────────
    st.markdown('<p class="section-label"><i class="lucide-trending-up" style="font-size:12px;margin-right:4px"></i> Investments</p>', unsafe_allow_html=True)
    portfolio_value = st.number_input("Current Portfolio Value ($)", min_value=0.0, value=0.0, step=500.0, key="portfolio")
    monthly_contribution = st.number_input("Monthly Contribution ($)", min_value=0.0, value=0.0, step=50.0, key="monthly_contrib")
    annual_return = st.slider("Expected Annual Return (%)", min_value=1.0, max_value=15.0, value=8.0, step=0.5, key="annual_return")
    time_horizon = st.slider("Time Horizon (years)", min_value=1, max_value=40, value=20, key="time_horizon")

    st.divider()

    # ── Risk Profile ──────────────────────────────────────────────────────
    st.markdown('<p class="section-label"><i class="lucide-shield" style="font-size:12px;margin-right:4px"></i> Risk Profile</p>', unsafe_allow_html=True)
    risk_profile = st.radio("Investment Risk Tolerance", ["Conservative", "Moderate", "Aggressive"], index=1, key="risk_profile")

    st.divider()

    # ── Analyze Button ────────────────────────────────────────────────────
    analyze_clicked = st.button("Analyze My Finances", type="primary", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# Run Analysis on Click
# ══════════════════════════════════════════════════════════════════════════════

if analyze_clicked:
    # Collect debts from session state
    debts = []
    for i in range(st.session_state.get("debt_count", 0)):
        d = {
            "name": st.session_state.get(f"debt_type_{i}", "Debt"),
            "balance": st.session_state.get(f"debt_bal_{i}", 0.0),
            "interest_rate": st.session_state.get(f"debt_rate_{i}", 0.0),
            "min_payment": st.session_state.get(f"debt_pay_{i}", 0.0),
        }
        if d["balance"] > 0:
            debts.append(d)
    st.session_state.debts = debts

    fin_data = {"income": income, "expenses": expenses, "debts": debts}
    errors = validate_financial_inputs(fin_data)

    if errors:
        for err in errors:
            st.sidebar.error(err)
    else:
        with st.spinner("Crunching your numbers…"):
            budget = calculate_budget_breakdown(income, expenses)
            savings = analyze_savings_rate(income, budget["surplus"])
            debt = compute_debt_metrics(debts, income)
            inv_df = project_investment_growth(portfolio_value, annual_return, time_horizon, monthly_contribution)

            health = score_financial_health({
                "savings_rate": savings["rate"],
                "dti": debt["dti"],
                "savings_potential": budget["savings_potential"],
                "has_investments": portfolio_value > 0 or monthly_contribution > 0,
            })

            report = generate_summary_report(budget, savings, debt, inv_df, health)

            st.session_state.financial_data = fin_data
            st.session_state.analysis_results = {
                "budget": budget,
                "savings": savings,
                "debt": debt,
                "investment_df": inv_df,
                "health_score": health,
                "report": report,
                "income": income,
                "expenses": expenses,
            }
        st.toast("Analysis complete!", icon="✅")


# ══════════════════════════════════════════════════════════════════════════════
# Main Content — Tabs
# ══════════════════════════════════════════════════════════════════════════════

tab_dashboard, tab_chat, tab_goals = st.tabs(["Dashboard", "AI Advisor", "Financial Goals"])

results = st.session_state.analysis_results

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — Dashboard
# ──────────────────────────────────────────────────────────────────────────────

with tab_dashboard:
    if results is None:
        st.info("Enter your financial data in the sidebar and click **Analyze My Finances** to get started.")
    else:
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
                st.plotly_chart(render_expense_pie_chart(non_zero_expenses), use_container_width=True)
            else:
                st.info("No expense data to visualize.")
        with c2:
            st.plotly_chart(
                render_income_vs_expense_bar(_income, budget["total_expenses"]),
                use_container_width=True,
            )

        # ── Chart Row 2 — Investment Growth ──────────────────────────────
        st.plotly_chart(render_investment_growth_line(inv_df), use_container_width=True)

        # ── Chart Row 3 ──────────────────────────────────────────────────
        c3, c4 = st.columns(2)
        with c3:
            if debt_met["payoff_timeline"]:
                debt_names = [d["name"] for d in debt_met["debts_detail"]]
                st.plotly_chart(
                    render_debt_payoff_timeline(debt_met["payoff_timeline"], debt_names),
                    use_container_width=True,
                )
            else:
                st.success("No debts — you're debt-free!")
        with c4:
            st.plotly_chart(render_financial_health_gauge(health), use_container_width=True)

        # ── Waterfall ────────────────────────────────────────────────────
        if non_zero_expenses:
            st.plotly_chart(render_budget_waterfall(_income, non_zero_expenses), use_container_width=True)

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


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — AI Advisor Chat
# ──────────────────────────────────────────────────────────────────────────────

with tab_chat:
    if not ai_advisor.is_available():
        st.warning(
            "**Gemini API key not configured.**  \n"
            "Add your key to the `.env` file to enable AI-powered advice.  \n"
            "The Dashboard and Goals tabs still work without it."
        )
    else:
        # Header with clear button
        hcol1, hcol2 = st.columns([4, 1])
        with hcol1:
            st.markdown(
                '<p style="font-size:16px;font-weight:600;color:#f0f0f5;margin:0">'
                '<i class="lucide-bot" style="margin-right:6px;color:#818cf8"></i>'
                'AI Financial Advisor</p>',
                unsafe_allow_html=True,
            )
        with hcol2:
            if st.button("Clear Chat", key="clear_chat"):
                st.session_state.chat_history = []
                st.rerun()

        # Build context from analysis
        financial_context = ""
        if results:
            financial_context = ai_advisor.build_financial_context(results["report"])

        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Quick prompts (shown when chat is empty)
        if not st.session_state.chat_history:
            st.caption("Try one of these prompts to get started:")
            qp1, qp2, qp3 = st.columns(3)
            quick_prompts = [
                "How can I reduce my debt faster?",
                "Am I saving enough for retirement?",
                "What's the best way to invest my surplus?",
            ]
            prompt_clicked = None
            with qp1:
                with st.container():
                    st.markdown('<div class="quick-prompt-btn">', unsafe_allow_html=True)
                    if st.button(quick_prompts[0], key="qp0"):
                        prompt_clicked = quick_prompts[0]
                    st.markdown('</div>', unsafe_allow_html=True)
            with qp2:
                with st.container():
                    st.markdown('<div class="quick-prompt-btn">', unsafe_allow_html=True)
                    if st.button(quick_prompts[1], key="qp1"):
                        prompt_clicked = quick_prompts[1]
                    st.markdown('</div>', unsafe_allow_html=True)
            with qp3:
                with st.container():
                    st.markdown('<div class="quick-prompt-btn">', unsafe_allow_html=True)
                    if st.button(quick_prompts[2], key="qp2"):
                        prompt_clicked = quick_prompts[2]
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            prompt_clicked = None

        # Chat input
        user_input = st.chat_input("Ask me anything about your finances…")
        active_prompt = user_input or prompt_clicked

        if active_prompt:
            # Show user message
            st.session_state.chat_history.append({"role": "user", "content": active_prompt})
            with st.chat_message("user"):
                st.markdown(active_prompt)

            # Stream AI response
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                for chunk in ai_advisor.generate_advice(
                    active_prompt,
                    st.session_state.chat_history[:-1],  # exclude current msg
                    financial_context,
                ):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)

            st.session_state.chat_history.append({"role": "assistant", "content": full_response})


# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — Financial Goals
# ──────────────────────────────────────────────────────────────────────────────

with tab_goals:
    st.markdown(
        '<p style="font-size:16px;font-weight:600;color:#f0f0f5;margin:0 0 12px 0">'
        '<i class="lucide-target" style="margin-right:6px;color:#818cf8"></i>'
        'Financial Goals</p>',
        unsafe_allow_html=True,
    )

    # ── Goal Creation Form ────────────────────────────────────────────────
    with st.expander("Add a New Goal", expanded=not st.session_state.goals):
        gc1, gc2 = st.columns(2)
        with gc1:
            goal_name = st.text_input("Goal Name", placeholder="e.g. Emergency Fund", key="goal_name_input")
            goal_amount = st.number_input("Target Amount ($)", min_value=0.0, step=500.0, key="goal_amount_input")
        with gc2:
            goal_date = st.date_input("Target Date", value=date(date.today().year + 1, 1, 1), key="goal_date_input")
            goal_priority = st.selectbox("Priority", ["High", "Medium", "Low"], key="goal_priority_input")

        goal_current = st.number_input("Current Savings Toward This Goal ($)", min_value=0.0, step=100.0, key="goal_current_input")

        if st.button("Save Goal", type="primary"):
            if not goal_name:
                st.error("Please enter a goal name.")
            elif goal_amount <= 0:
                st.error("Target amount must be greater than zero.")
            elif len(st.session_state.goals) >= 5:
                st.warning("Maximum of 5 concurrent goals. Remove one before adding another.")
            else:
                st.session_state.goals.append({
                    "name": goal_name,
                    "target_amount": goal_amount,
                    "target_date": goal_date.isoformat(),
                    "priority": goal_priority,
                    "current_savings": goal_current,
                })
                st.toast(f"Goal '{goal_name}' saved!")
                st.rerun()

    # ── Display Active Goals ──────────────────────────────────────────────
    if st.session_state.goals:
        st.plotly_chart(render_savings_progress_bar(st.session_state.goals), use_container_width=True)

        for idx, goal in enumerate(st.session_state.goals):
            target = goal["target_amount"]
            current = goal.get("current_savings", 0)
            remaining = target - current
            target_date = datetime.fromisoformat(goal["target_date"]).date()
            months_left = max((target_date.year - date.today().year) * 12 + (target_date.month - date.today().month), 1)
            monthly_needed = remaining / months_left if remaining > 0 else 0

            # Feasibility check
            surplus = 0
            if results:
                surplus = results["budget"].get("surplus", 0)

            if remaining <= 0:
                feasibility = "Achieved"
                feas_class = "feasibility-achievable"
            elif surplus >= monthly_needed:
                feasibility = "Achievable"
                feas_class = "feasibility-achievable"
            elif surplus >= monthly_needed * 0.5:
                feasibility = "At Risk"
                feas_class = "feasibility-at-risk"
            else:
                feasibility = "Not Feasible"
                feas_class = "feasibility-not-feasible"

            st.markdown(
                f"""<div class="goal-card">
                    <h4>{goal['name']}  <span class="{feas_class}" style="float:right">{feasibility}</span></h4>
                    <p>Target: {format_currency(target)} &nbsp;|&nbsp; By: {goal['target_date']} &nbsp;|&nbsp;
                    Priority: {goal['priority']}</p>
                    <p>Monthly savings needed: <strong>{format_currency(monthly_needed)}</strong> &nbsp;|&nbsp;
                    Progress: {format_currency(current)} / {format_currency(target)}</p>
                </div>""",
                unsafe_allow_html=True,
            )

            gcol1, gcol2 = st.columns([1, 1])
            with gcol1:
                if ai_advisor.is_available():
                    if st.button("Generate AI Plan", key=f"plan_{idx}"):
                        with st.spinner("Generating your personalized plan…"):
                            plan = ai_advisor.generate_financial_plan(
                                [goal],
                                results["report"] if results else {},
                            )
                        st.markdown(plan)
            with gcol2:
                if st.button("Remove Goal", key=f"del_{idx}"):
                    st.session_state.goals.pop(idx)
                    st.rerun()

        st.divider()

    # ── Retirement Calculator ─────────────────────────────────────────────
    st.markdown(
        '<p style="font-size:16px;font-weight:600;color:#f0f0f5;margin:0 0 12px 0">'
        '<i class="lucide-sunset" style="margin-right:6px;color:#fb923c"></i>'
        'Retirement Calculator</p>',
        unsafe_allow_html=True,
    )
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        current_age = st.number_input("Current Age", min_value=18, max_value=80, value=30, key="ret_age")
        retirement_age = st.number_input("Retirement Age", min_value=current_age + 1, max_value=85, value=65, key="ret_retire_age")
    with rc2:
        desired_monthly = st.number_input("Desired Monthly Retirement Income ($)", min_value=0.0, value=4000.0, step=500.0, key="ret_monthly")
        social_security = st.number_input("Expected Social Security / Pension ($/mo)", min_value=0.0, value=1500.0, step=100.0, key="ret_ss")
    with rc3:
        ret_return = st.slider("Expected Return During Retirement (%)", 2.0, 10.0, 5.0, 0.5, key="ret_return")
        inflation = st.slider("Expected Inflation (%)", 1.0, 6.0, 3.0, 0.5, key="ret_inflation")

    if st.button("Calculate Retirement Projection", type="primary"):
        years_to_retire = retirement_age - current_age
        monthly_gap = desired_monthly - social_security
        if monthly_gap <= 0:
            st.success("Your Social Security / pension covers your desired retirement income!")
        else:
            annual_gap = monthly_gap * 12
            real_return = ((1 + ret_return / 100) / (1 + inflation / 100)) - 1
            if real_return <= 0:
                nest_egg = annual_gap * 30  # simple fallback
            else:
                nest_egg = annual_gap / real_return  # perpetuity-style estimate

            # Current trajectory
            current_portfolio = results["investment_df"].iloc[-1]["total_value"] if results else 0
            gap = max(nest_egg - current_portfolio, 0)

            st.markdown("---")
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("Required Nest Egg", format_currency(nest_egg))
            with r2:
                st.metric("Current Trajectory", format_currency(current_portfolio))
            with r3:
                st.metric("Gap", format_currency(gap), delta="On Track" if gap == 0 else "Shortfall", delta_color="normal" if gap == 0 else "inverse")

            if gap > 0 and years_to_retire > 0:
                monthly_extra = gap / (years_to_retire * 12)
                st.info(f"To close the gap, aim to save an additional **{format_currency(monthly_extra)}/month** over the next {years_to_retire} years (not accounting for compounding on the extra savings).")
