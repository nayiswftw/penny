"""
goals.py — Financial Goals Tab
───────────────────────────────
Goal creation, tracking with feasibility indicators,
AI-powered plans, and a retirement calculator.
"""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from penny import ai_advisor
from penny.utils.formatting import format_currency
from penny.visualization import render_savings_progress_bar


def render_goals(results: dict | None) -> None:
    """Render the Financial Goals tab."""
    st.markdown(
        '<p style="font-size:16px;font-weight:600;color:#f0f0f5;margin:0 0 12px 0">'
        '<i class="lucide-target" style="margin-right:6px;color:#818cf8"></i>'
        "Financial Goals</p>",
        unsafe_allow_html=True,
    )

    # ── Goal Creation Form ────────────────────────────────────────────
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

    # ── Display Active Goals ──────────────────────────────────────────
    if st.session_state.goals:
        st.plotly_chart(render_savings_progress_bar(st.session_state.goals), width="stretch")

        for idx, goal in enumerate(st.session_state.goals):
            target = goal["target_amount"]
            current = goal.get("current_savings", 0)
            remaining = target - current
            target_date = datetime.fromisoformat(goal["target_date"]).date()
            months_left = max(
                (target_date.year - date.today().year) * 12 + (target_date.month - date.today().month),
                1,
            )
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
                if ai_advisor.is_available() and st.button("Generate AI Plan", key=f"plan_{idx}"):
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

    # ── Retirement Calculator ─────────────────────────────────────────
    st.markdown(
        '<p style="font-size:16px;font-weight:600;color:#f0f0f5;margin:0 0 12px 0">'
        '<i class="lucide-sunset" style="margin-right:6px;color:#fb923c"></i>'
        "Retirement Calculator</p>",
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
                st.metric(
                    "Gap",
                    format_currency(gap),
                    delta="On Track" if gap == 0 else "Shortfall",
                    delta_color="normal" if gap == 0 else "inverse",
                )

            if gap > 0 and years_to_retire > 0:
                monthly_extra = gap / (years_to_retire * 12)
                st.info(
                    f"To close the gap, aim to save an additional **{format_currency(monthly_extra)}/month** "
                    f"over the next {years_to_retire} years (not accounting for compounding on the extra savings)."
                )
