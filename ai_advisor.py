"""
ai_advisor.py — Gemini AI Financial Guidance Module
────────────────────────────────────────────────────
Manages all communication with Google Gemini, constructs
context-rich prompts, maintains conversation history, and
returns structured financial guidance.
"""

from __future__ import annotations

import time
import traceback
from typing import Generator

from utils import load_env_config, sanitize_user_input, log_api_usage, logger

# ─── Config ───────────────────────────────────────────────────────────────────

_config = load_env_config()
_HAS_API_KEY = bool(_config["GEMINI_API_KEY"]) and _config["GEMINI_API_KEY"] != "your_google_gemini_api_key_here"

# Lazy SDK import — only if key is available
_genai = None
_model = None


def _ensure_model():
    """Lazily initialize the Gemini model on first use."""
    global _genai, _model
    if _model is not None:
        return _model
    if not _HAS_API_KEY:
        raise RuntimeError("Gemini API key is not configured. Add it to your .env file.")
    import google.generativeai as genai
    _genai = genai
    genai.configure(api_key=_config["GEMINI_API_KEY"])
    _model = genai.GenerativeModel(
        model_name=_config["GEMINI_MODEL"],
        generation_config=genai.GenerationConfig(
            max_output_tokens=_config["GEMINI_MAX_TOKENS"],
            temperature=_config["GEMINI_TEMPERATURE"],
        ),
    )
    return _model


# ─── System Prompt ────────────────────────────────────────────────────────────

def build_system_prompt() -> str:
    """Construct the system prompt defining the advisor persona."""
    return (
        "You are an expert, empathetic AI Financial Advisor with CFP-level knowledge. "
        "Your tone is warm, professional, and non-judgmental.\n\n"
        "RULES:\n"
        "• Always reference the user's specific financial data when giving advice.\n"
        "• Express all monetary values in the user's currency.\n"
        "• For complex answers, use clear section headers, bullet points, and actionable next steps.\n"
        "• Recommend consulting a qualified professional for tax, legal, or complex investment decisions.\n"
        "• NEVER recommend specific stock tickers, gambling strategies, or illegal financial activities.\n"
        "• If you don't have enough information, ask clarifying questions before advising.\n"
    )


# ─── Context Builder ─────────────────────────────────────────────────────────

def build_financial_context(metrics: dict) -> str:
    """Convert analysis metrics into a readable context string for prompts."""
    if not metrics:
        return "No financial data has been provided yet."

    lines = [
        "=== CURRENT FINANCIAL SNAPSHOT ===",
        f"Monthly Surplus / Deficit: ${metrics.get('monthly_income_surplus', 0):,.2f}",
        f"Total Monthly Expenses: ${metrics.get('total_expenses', 0):,.2f}",
        f"Savings Rate: {metrics.get('savings_rate', 0):.1f}%  ({metrics.get('savings_status', '')})",
        f"Debt-to-Income Ratio: {metrics.get('dti', 0):.1f}%",
        f"Total Outstanding Debt: ${metrics.get('total_debt', 0):,.2f}",
        f"Financial Health Score: {metrics.get('health_score', 0)} / 100",
    ]

    ratios = metrics.get("expense_ratios", {})
    if ratios:
        lines.append("\nExpense Breakdown (% of income):")
        for cat, pct in ratios.items():
            lines.append(f"  • {cat}: {pct:.1f}%")

    projected = metrics.get("projected_portfolio")
    if projected:
        lines.append(f"\nProjected Portfolio Value: ${projected:,.2f}")
        lines.append(f"  Total Contributions: ${metrics.get('total_contributions', 0):,.2f}")
        lines.append(f"  Total Returns: ${metrics.get('total_returns', 0):,.2f}")

    return "\n".join(lines)


# ─── Core API Methods ─────────────────────────────────────────────────────────

def is_available() -> bool:
    """Return True if the Gemini API key is configured."""
    return _HAS_API_KEY


def generate_advice(
    user_message: str,
    chat_history: list[dict],
    financial_context: str,
) -> Generator[str, None, None]:
    """Send a multi-turn conversation to Gemini and yield streamed text chunks.

    Parameters
    ----------
    user_message : str
        The latest user message.
    chat_history : list[dict]
        List of ``{"role": "user"|"assistant", "content": str}`` dicts.
    financial_context : str
        The structured financial snapshot injected as context.

    Yields
    ------
    str
        Successive text chunks as they arrive from the Gemini stream.
    """
    model = _ensure_model()
    user_message = sanitize_user_input(user_message)

    system_prompt = build_system_prompt()
    context_block = f"\n\n{financial_context}\n\n" if financial_context else ""

    # Build Gemini contents list
    contents = []
    # First turn carries system prompt + context
    first_user = f"{system_prompt}{context_block}{user_message}" if not chat_history else None

    # Replay history (cap at 10 turns for token efficiency)
    recent_history = chat_history[-10:]
    for i, msg in enumerate(recent_history):
        role = "user" if msg["role"] == "user" else "model"
        text = msg["content"]
        if i == 0 and role == "user":
            text = f"{system_prompt}{context_block}{text}"
        contents.append({"role": role, "parts": [text]})

    # Append current message
    current_text = first_user if first_user else f"{context_block}{user_message}" if not recent_history else user_message
    contents.append({"role": "user", "parts": [current_text]})

    start = time.perf_counter()
    try:
        response = model.generate_content(contents, stream=True)
        full_text = ""
        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                yield chunk.text
        latency_ms = (time.perf_counter() - start) * 1000
        # Log usage
        usage = getattr(response, "usage_metadata", None)
        if usage:
            log_api_usage(
                getattr(usage, "prompt_token_count", 0),
                getattr(usage, "candidates_token_count", 0),
                latency_ms,
            )
    except Exception as exc:
        logger.error("Gemini API error: %s\n%s", exc, traceback.format_exc())
        yield f"\n\n⚠️ Sorry, I encountered an error: {exc}. Please try again."


def generate_financial_plan(goals: list[dict], metrics: dict) -> str:
    """Generate a structured financial plan for the given goals.

    Parameters
    ----------
    goals : list[dict]
        Each goal has: name, target_amount, target_date, priority.
    metrics : dict
        Current financial summary from generate_summary_report().

    Returns
    -------
    str  The AI-generated plan text.
    """
    model = _ensure_model()
    context = build_financial_context(metrics)

    goals_text = "\n".join(
        f"- {g['name']}: ${g['target_amount']:,.2f} by {g['target_date']} (Priority: {g['priority']})"
        for g in goals
    )

    prompt = (
        f"{build_system_prompt()}\n\n"
        f"{context}\n\n"
        "The user has defined the following financial goals:\n"
        f"{goals_text}\n\n"
        "Please create a detailed, actionable financial plan with:\n"
        "1. A prioritized timeline for achieving each goal\n"
        "2. Specific monthly savings targets\n"
        "3. Recommended allocation changes\n"
        "4. Risk considerations and contingency suggestions\n"
        "5. Milestone checkpoints\n\n"
        "Use clear section headers and bullet points."
    )

    start = time.perf_counter()
    try:
        response = model.generate_content(prompt)
        latency_ms = (time.perf_counter() - start) * 1000
        usage = getattr(response, "usage_metadata", None)
        if usage:
            log_api_usage(
                getattr(usage, "prompt_token_count", 0),
                getattr(usage, "candidates_token_count", 0),
                latency_ms,
            )
        return response.text
    except Exception as exc:
        logger.error("Gemini plan generation error: %s", exc)
        return f"⚠️ Could not generate plan: {exc}"


def analyze_spending_patterns(expense_data: dict, income: float) -> str:
    """Ask Gemini for AI-driven commentary on spending habits.

    Parameters
    ----------
    expense_data : dict
        Category → amount mapping.
    income : float
        Monthly income for ratio context.

    Returns
    -------
    str  AI commentary text.
    """
    model = _ensure_model()

    breakdown = "\n".join(
        f"  • {cat}: ${amt:,.2f} ({amt/income*100:.1f}% of income)" if income > 0
        else f"  • {cat}: ${amt:,.2f}"
        for cat, amt in expense_data.items()
    )

    prompt = (
        f"{build_system_prompt()}\n\n"
        f"Monthly Income: ${income:,.2f}\n"
        f"Expense Breakdown:\n{breakdown}\n\n"
        "Provide a concise analysis of these spending patterns:\n"
        "1. Which categories seem high relative to income?\n"
        "2. What specific optimizations could reduce spending?\n"
        "3. Are there any concerning patterns?\n"
        "Keep the response under 300 words."
    )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        logger.error("Spending analysis error: %s", exc)
        return f"⚠️ Could not analyze spending: {exc}"
