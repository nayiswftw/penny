"""
visualization.py — Plotly Chart Library for Financial Data
──────────────────────────────────────────────────────────
Seven chart components consumed by the Streamlit dashboard.
All charts follow a consistent dark theme and brand palette.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

# ─── Theme Configuration ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class Theme:
    """Centralised chart theme constants."""

    accent: str = "#818cf8"
    positive: str = "#34d399"
    negative: str = "#f87171"
    warning: str = "#fbbf24"
    surface: str = "#16161f"
    border: str = "rgba(255,255,255,0.06)"
    muted: str = "#8a8a9a"
    text: str = "#f0f0f5"
    colors: tuple[str, ...] = (
        "#818cf8", "#34d399", "#fb923c", "#a855f7",
        "#22d3ee", "#f472b6", "#fbbf24", "#6366f1",
    )
    font_family: str = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"


THEME = Theme()

_LAYOUT_DEFAULTS = dict(
    font=dict(family=THEME.font_family, size=13, color=THEME.muted),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=40, t=50, b=40),
    legend=dict(
        font=dict(size=11),
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(255,255,255,0.1)",
    ),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
)


def _base_layout(**overrides) -> dict:
    """Return a copy of _LAYOUT_DEFAULTS merged with *overrides*."""
    layout = {}
    for k, v in _LAYOUT_DEFAULTS.items():
        if isinstance(v, dict):
            merged = {**v, **overrides.pop(k, {})}
            layout[k] = merged
        else:
            layout[k] = overrides.pop(k, v)
    layout.update(overrides)
    return layout


# ─── 1. Expense Donut Chart ──────────────────────────────────────────────────


def render_expense_pie_chart(expenses: dict[str, float]) -> go.Figure:
    """Donut chart showing expense distribution by category."""
    fig = go.Figure(go.Pie(
        labels=list(expenses.keys()),
        values=list(expenses.values()),
        hole=0.55,
        marker=dict(colors=list(THEME.colors[: len(expenses)])),
        textinfo="percent+label",
        textfont_size=11,
        hovertemplate="%{label}: $%{value:,.2f}<extra></extra>",
    ))
    fig.update_layout(**_base_layout(title="Expense Breakdown"))
    return fig


# ─── 2. Income vs Expense Bar Chart ──────────────────────────────────────────


def render_income_vs_expense_bar(income: float, total_expenses: float) -> go.Figure:
    """Side-by-side bar chart comparing income to total expenses."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Income"], y=[income], name="Income",
        marker_color=THEME.positive, text=[f"${income:,.0f}"], textposition="outside",
    ))
    fig.add_trace(go.Bar(
        x=["Expenses"], y=[total_expenses], name="Expenses",
        marker_color=THEME.negative, text=[f"${total_expenses:,.0f}"], textposition="outside",
    ))
    fig.update_layout(**_base_layout(
        title="Income vs Expenses",
        barmode="group",
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)", title="Amount ($)"),
        showlegend=False,
    ))
    return fig


# ─── 3. Investment Growth Line / Area Chart ──────────────────────────────────


def render_investment_growth_line(projection_df: pd.DataFrame) -> go.Figure:
    """Multi-line area chart showing investment growth over time."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=projection_df["year"], y=projection_df["total_value"],
        name="Total Value", fill="tozeroy",
        line=dict(color=THEME.accent, width=2),
        hovertemplate="Year %{x}: $%{y:,.0f}<extra>Total Value</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=projection_df["year"], y=projection_df["contributions"],
        name="Contributions", fill="tozeroy",
        line=dict(color=THEME.positive, width=2, dash="dot"),
        hovertemplate="Year %{x}: $%{y:,.0f}<extra>Contributions</extra>",
    ))
    fig.update_layout(**_base_layout(
        title="Investment Growth Projection",
        xaxis=dict(title="Year", gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
        yaxis=dict(title="Value ($)", gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
    ))
    return fig


# ─── 4. Debt Payoff Timeline ─────────────────────────────────────────────────


def render_debt_payoff_timeline(payoff_timeline: list[dict], debt_names: list[str]) -> go.Figure:
    """Stacked area chart illustrating debt payoff trajectory."""
    df = pd.DataFrame(payoff_timeline)
    fig = go.Figure()
    for i, name in enumerate(debt_names):
        if name in df.columns:
            fig.add_trace(go.Scatter(
                x=df["month"], y=df[name],
                name=name, stackgroup="debt",
                line=dict(color=THEME.colors[i % len(THEME.colors)]),
                hovertemplate=f"{name}: $%{{y:,.0f}} (Month %{{x}})<extra></extra>",
            ))
    fig.update_layout(**_base_layout(
        title="Debt Payoff Timeline",
        xaxis=dict(title="Month", gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
        yaxis=dict(title="Balance ($)", gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
    ))
    return fig


# ─── 5. Financial Health Gauge ────────────────────────────────────────────────


def render_financial_health_gauge(score: int) -> go.Figure:
    """Gauge / speedometer chart for the composite health score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title=dict(text="Financial Health Score", font=dict(size=16, color=THEME.text)),
        number=dict(font=dict(size=40, color=THEME.text)),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(color=THEME.muted)),
            bar=dict(color=THEME.accent),
            bgcolor="rgba(255,255,255,0.03)",
            steps=[
                dict(range=[0, 40], color="rgba(248,113,113,0.2)"),
                dict(range=[40, 70], color="rgba(251,191,36,0.2)"),
                dict(range=[70, 100], color="rgba(52,211,153,0.2)"),
            ],
        ),
    ))
    fig.update_layout(**_base_layout(height=300))
    return fig


# ─── 6. Savings Progress Bar ─────────────────────────────────────────────────


def render_savings_progress_bar(goals: list[dict]) -> go.Figure:
    """Horizontal bar chart displaying progress toward each savings goal."""
    names = [g["name"] for g in goals]
    targets = [g["target_amount"] for g in goals]
    currents = [g.get("current_savings", 0) for g in goals]
    pcts = [min(c / t * 100, 100) if t > 0 else 0 for c, t in zip(currents, targets)]

    fig = go.Figure()
    # Background (remaining)
    fig.add_trace(go.Bar(
        y=names, x=[100] * len(names),
        orientation="h", name="Remaining",
        marker=dict(color="rgba(255,255,255,0.05)"),
        hoverinfo="skip",
    ))
    # Progress
    fig.add_trace(go.Bar(
        y=names, x=pcts,
        orientation="h", name="Progress",
        marker=dict(
            color=[THEME.positive if p >= 100 else THEME.accent for p in pcts],
        ),
        text=[f"{p:.0f}%" for p in pcts],
        textposition="inside",
        hovertemplate="%{y}: %{x:.1f}% complete<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        title="Goal Progress",
        barmode="overlay",
        xaxis=dict(
            range=[0, 105], title="Progress (%)",
            gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)",
        ),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
        showlegend=False,
        height=max(200, 60 * len(names)),
    ))
    return fig


# ─── 7. Budget Waterfall Chart ────────────────────────────────────────────────


def render_budget_waterfall(income: float, expenses: dict[str, float]) -> go.Figure:
    """Waterfall chart showing how income flows through expenses to net savings."""
    categories = ["Income", *list(expenses.keys()), "Net Savings"]
    values = [income] + [-v for v in expenses.values()] + [0]  # net computed by waterfall
    measures = ["absolute"] + ["relative"] * len(expenses) + ["total"]

    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        measure=measures,
        connector=dict(line=dict(color="rgba(255,255,255,0.1)")),
        increasing=dict(marker=dict(color=THEME.positive)),
        decreasing=dict(marker=dict(color=THEME.negative)),
        totals=dict(marker=dict(color=THEME.accent)),
        textposition="outside",
        text=[f"${abs(v):,.0f}" if v != 0 else "" for v in values],
    ))
    fig.update_layout(**_base_layout(
        title="Budget Flow (Waterfall)",
        yaxis=dict(title="Amount ($)", gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
        showlegend=False,
    ))
    return fig
