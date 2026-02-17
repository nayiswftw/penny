"""
visualization.py — Plotly Chart Library for Financial Data
──────────────────────────────────────────────────────────
Seven interactive chart components with brand-consistent
styling, hover tooltips, and responsive layout.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ─── Brand Palette ────────────────────────────────────────────────────────────

COLORS = {
    "primary": "#6366f1",
    "interactive": "#818cf8",
    "success": "#34d399",
    "warning": "#fb923c",
    "danger": "#f87171",
    "surface": "#16161f",
    "border": "rgba(255,255,255,0.06)",
    "muted": "#8a8a9a",
    "text": "#f0f0f5",
}

CHART_COLORS = [
    "#818cf8", "#34d399", "#fb923c", "#a855f7",
    "#22d3ee", "#f472b6", "#fbbf24", "#6366f1",
]

_LAYOUT_DEFAULTS = dict(
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", size=13, color="#8a8a9a"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=40, t=50, b=40),
    hoverlabel=dict(
        bgcolor="#1e1e2a",
        font_size=12,
        font_family="Inter",
        font_color="#f0f0f5",
        bordercolor="rgba(255,255,255,0.1)",
    ),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
)


def _base_layout(**overrides) -> dict:
    layout = {**_LAYOUT_DEFAULTS, **overrides}
    # Ensure title and legend text are light on dark backgrounds
    if "title" in layout and isinstance(layout["title"], str):
        layout["title"] = dict(text=layout["title"], font=dict(color="#f0f0f5", size=16))
    if "legend" not in layout:
        layout["legend"] = dict(font=dict(color="#8a8a9a"))
    else:
        layout["legend"].setdefault("font", {})["color"] = "#8a8a9a"
    return layout


# ─── 1. Expense Donut Chart ──────────────────────────────────────────────────

def render_expense_pie_chart(expenses: dict[str, float]) -> go.Figure:
    """Donut chart showing expense distribution by category."""
    categories = list(expenses.keys())
    values = list(expenses.values())

    fig = go.Figure(go.Pie(
        labels=categories,
        values=values,
        hole=0.55,
        marker=dict(colors=CHART_COLORS[:len(categories)]),
        textinfo="label+percent",
        textfont_size=12,
        hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout(title="Expense Breakdown",
                       legend=dict(orientation="h", y=-0.15, font=dict(color="#8a8a9a"))),
        showlegend=True,
    )
    return fig


# ─── 2. Income vs Expense Bar Chart ──────────────────────────────────────────

def render_income_vs_expense_bar(income: float, total_expenses: float) -> go.Figure:
    """Side-by-side bar chart comparing income to total expenses."""
    surplus = income - total_expenses
    categories = ["Income", "Expenses", "Surplus / Deficit"]
    values = [income, total_expenses, surplus]
    colors = [COLORS["interactive"], COLORS["danger"], COLORS["success"] if surplus >= 0 else COLORS["danger"]]

    fig = go.Figure(go.Bar(
        x=categories,
        y=values,
        marker_color=colors,
        text=[f"${v:,.0f}" for v in values],
        textposition="outside",
        textfont=dict(color="#f0f0f5"),
        hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout(title="Income vs. Expenses"),
        yaxis_title="Amount ($)",
        showlegend=False,
    )
    return fig


# ─── 3. Investment Growth Line / Area Chart ──────────────────────────────────

def render_investment_growth_line(projection_df: pd.DataFrame) -> go.Figure:
    """Multi-line area chart showing investment growth over time."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=projection_df["year"],
        y=projection_df["contributions"],
        name="Contributions",
        fill="tozeroy",
        mode="lines",
        line=dict(color=COLORS["interactive"], width=2),
        hovertemplate="Year %{x}<br>Contributions: $%{y:,.0f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=projection_df["year"],
        y=projection_df["total_value"],
        name="Total Value",
        fill="tonexty",
        mode="lines",
        line=dict(color=COLORS["success"], width=2),
        hovertemplate="Year %{x}<br>Total: $%{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout(title="Investment Growth Projection",
                       legend=dict(orientation="h", y=-0.15, font=dict(color="#8a8a9a"))),
        xaxis_title="Year",
        yaxis_title="Value ($)",
    )
    return fig


# ─── 4. Debt Payoff Timeline ─────────────────────────────────────────────────

def render_debt_payoff_timeline(payoff_timeline: list[dict], debt_names: list[str]) -> go.Figure:
    """Stacked area chart illustrating debt payoff trajectory."""
    if not payoff_timeline:
        fig = go.Figure()
        fig.update_layout(**_base_layout(title="Debt Payoff Timeline"))
        fig.add_annotation(text="No debt data available", showarrow=False, font_size=14)
        return fig

    df = pd.DataFrame(payoff_timeline)
    fig = go.Figure()

    for i, name in enumerate(debt_names):
        if name in df.columns:
            fig.add_trace(go.Scatter(
                x=df["month"],
                y=df[name],
                name=name,
                stackgroup="one",
                line=dict(color=CHART_COLORS[i % len(CHART_COLORS)]),
                hovertemplate=f"<b>{name}</b><br>Month %{{x}}<br>${{y:,.0f}} remaining<extra></extra>",
            ))

    fig.update_layout(
        **_base_layout(title="Debt Payoff Timeline",
                       legend=dict(orientation="h", y=-0.15, font=dict(color="#8a8a9a"))),
        xaxis_title="Month",
        yaxis_title="Remaining Balance ($)",
    )
    return fig


# ─── 5. Financial Health Gauge ────────────────────────────────────────────────

def render_financial_health_gauge(score: int) -> go.Figure:
    """Gauge / speedometer chart for the composite health score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Financial Health Score", "font": {"size": 16, "color": "#8a8a9a"}},
        number={"font": {"size": 42, "color": "#f0f0f5"}},
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#8a8a9a", dtick=20),
            bar=dict(color=COLORS["primary"]),
            bgcolor="#1e1e2a",
            borderwidth=0,
            steps=[
                dict(range=[0, 40], color="rgba(248,113,113,0.15)"),
                dict(range=[40, 70], color="rgba(251,146,60,0.15)"),
                dict(range=[70, 100], color="rgba(52,211,153,0.15)"),
            ],
            threshold=dict(
                line=dict(color=COLORS["success"] if score >= 70 else COLORS["warning"] if score >= 40 else COLORS["danger"], width=3),
                thickness=0.8,
                value=score,
            ),
        ),
    ))

    fig.update_layout(**_base_layout(), height=300)
    return fig


# ─── 6. Savings Progress Bar ─────────────────────────────────────────────────

def render_savings_progress_bar(goals: list[dict]) -> go.Figure:
    """Horizontal bar chart displaying progress toward each savings goal."""
    if not goals:
        fig = go.Figure()
        fig.update_layout(**_base_layout(title="Goal Progress"))
        fig.add_annotation(text="No goals defined", showarrow=False, font_size=14)
        return fig

    names = [g["name"] for g in goals]
    current = [g.get("current_savings", 0) for g in goals]
    targets = [g["target_amount"] for g in goals]
    pcts = [min((c / t) * 100, 100) if t > 0 else 0 for c, t in zip(current, targets)]

    fig = go.Figure()

    # Background (remaining)
    fig.add_trace(go.Bar(
        y=names, x=[100] * len(names),
        orientation="h",
        marker_color=COLORS["border"],
        showlegend=False,
        hoverinfo="skip",
    ))

    # Progress
    fig.add_trace(go.Bar(
        y=names, x=pcts,
        orientation="h",
        marker_color=[COLORS["success"] if p >= 100 else COLORS["interactive"] for p in pcts],
        text=[f"{p:.0f}%" for p in pcts],
        textposition="inside",
        showlegend=False,
        hovertemplate="<b>%{y}</b><br>%{x:.1f}% complete<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout(
            title="Goal Progress",
            xaxis=dict(visible=False, range=[0, 105]),
            yaxis=dict(autorange="reversed"),
        ),
        barmode="overlay",
        height=max(200, len(goals) * 60 + 80),
    )
    return fig


# ─── 7. Budget Waterfall Chart ────────────────────────────────────────────────

def render_budget_waterfall(income: float, expenses: dict[str, float]) -> go.Figure:
    """Waterfall chart showing how income flows through expenses to net savings."""
    categories = ["Income"] + list(expenses.keys()) + ["Net Savings"]
    values = [income] + [-v for v in expenses.values()] + [0]  # last is computed
    measures = ["absolute"] + ["relative"] * len(expenses) + ["total"]

    net = income - sum(expenses.values())

    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        measure=measures,
        connector=dict(line=dict(color=COLORS["border"])),
        increasing=dict(marker_color=COLORS["success"]),
        decreasing=dict(marker_color=COLORS["danger"]),
        totals=dict(marker_color=COLORS["primary"]),
        textposition="outside",
        text=[f"${abs(v):,.0f}" if v != 0 else f"${abs(net):,.0f}" for v in values],
        hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout(title="Budget Waterfall"),
        yaxis_title="Amount ($)",
        showlegend=False,
    )
    return fig
