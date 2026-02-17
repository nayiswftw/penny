"""
app.py — Penny: AI Financial Advisor (Streamlit)
─────────────────────────────────────────────────
Slim application entrypoint.
Delegates to page modules for sidebar, dashboard, chat, and goals.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the `src/` directory is on sys.path so `penny` is importable
# when running via `streamlit run src/penny/app.py` without pip install.
_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import streamlit as st

from penny.finance_analysis import (
    analyze_savings_rate,
    calculate_budget_breakdown,
    compute_debt_metrics,
    generate_summary_report,
    project_investment_growth,
    score_financial_health,
)
from penny.views.chat import render_chat
from penny.views.dashboard import render_dashboard
from penny.views.goals import render_goals
from penny.views.sidebar import render_sidebar
from penny.utils.validation import validate_financial_inputs

# ══════════════════════════════════════════════════════════════════════════════
# Page Config  (MUST be the first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════

_LOGO_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "logo.png"

st.set_page_config(
    page_title="Penny — AI Financial Advisor",
    page_icon=str(_LOGO_PATH),
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lucide Icons CDN ──────────────────────────────────────────────────────────
st.markdown(
    "<style>@import url('https://unpkg.com/lucide-static@latest/font/lucide.css');</style>",
    unsafe_allow_html=True,
)

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS: dict = {
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
# Sidebar — Data Entry
# ══════════════════════════════════════════════════════════════════════════════

(
    income,
    expenses,
    portfolio_value,
    monthly_contribution,
    annual_return,
    time_horizon,
    risk_profile,
    analyze_clicked,
) = render_sidebar()

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

with tab_dashboard:
    render_dashboard(results)

with tab_chat:
    render_chat(results)

with tab_goals:
    render_goals(results)
