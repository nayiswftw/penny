"""
ai_advisor.py — Gemini AI Financial Guidance Module
────────────────────────────────────────────────────
Manages all communication with Google Gemini, constructs
context-rich prompts, maintains conversation history, and
returns structured financial guidance.

Uses the new `google-genai` SDK (replaces deprecated
`google-generativeai`).
"""

from __future__ import annotations

import time
import traceback
from typing import TYPE_CHECKING

from penny.config import get_settings, logger
from penny.exceptions import GeminiAPIError, GeminiRateLimitError
from penny.utils.sanitize import sanitize_user_input

if TYPE_CHECKING:
    from collections.abc import Generator

# ─── Constants ────────────────────────────────────────────────────────────────

MAX_HISTORY_TURNS = 10
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds

# ─── Lazy client initialisation ──────────────────────────────────────────────

_client = None


def _ensure_client():
    """Lazily initialise the google.genai Client on first use."""
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    if not settings.has_api_key:
        raise GeminiAPIError("Gemini API key is not configured. Add it to your .env file.")

    from google import genai

    _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _get_config():
    """Build a GenerateContentConfig from app settings."""
    from google.genai import types

    settings = get_settings()
    return types.GenerateContentConfig(
        max_output_tokens=settings.gemini_max_tokens,
        temperature=settings.gemini_temperature,
    )


def _call_with_retry(fn, *args, **kwargs):
    """Execute *fn* with exponential-backoff retries for transient errors."""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            err_str = str(exc).lower()
            # Rate limit or transient server errors — retry
            if "429" in err_str or "resource exhausted" in err_str:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning("Rate limited (attempt %d/%d), retrying in %.1fs", attempt + 1, MAX_RETRIES, delay)
                time.sleep(delay)
                continue
            if "503" in err_str or "unavailable" in err_str:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning("Service unavailable (attempt %d/%d), retrying in %.1fs", attempt + 1, MAX_RETRIES, delay)
                time.sleep(delay)
                continue
            # Non-retryable error — raise immediately
            raise GeminiAPIError(str(exc)) from exc
    # Exhausted retries
    if last_exc and ("429" in str(last_exc).lower() or "resource exhausted" in str(last_exc).lower()):
        raise GeminiRateLimitError(f"Rate limit exceeded after {MAX_RETRIES} retries: {last_exc}") from last_exc
    raise GeminiAPIError(f"API call failed after {MAX_RETRIES} retries: {last_exc}") from last_exc


# ─── System Prompt ────────────────────────────────────────────────────────────


def build_system_prompt() -> str:
    """Construct the system prompt defining the advisor persona."""
    return (
        "You are an expert, empathetic AI Financial Advisor with CFP-level knowledge. "
        "Your tone is warm, professional, and non-judgmental.\n\n"
        "RULES:\n"
        "- Always reference the user's specific financial data when giving advice.\n"
        "- Express all monetary values in the user's currency.\n"
        "- For complex answers, use clear section headers, bullet points, and actionable next steps.\n"
        "- Recommend consulting a qualified professional for tax, legal, or complex investment decisions.\n"
        "- NEVER recommend specific stock tickers, gambling strategies, or illegal financial activities.\n"
        "- If you don't have enough information, ask clarifying questions before advising.\n"
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
            lines.append(f"  - {cat}: {pct:.1f}%")

    projected = metrics.get("projected_portfolio")
    if projected:
        lines.append(f"\nProjected Portfolio Value: ${projected:,.2f}")
        lines.append(f"  Total Contributions: ${metrics.get('total_contributions', 0):,.2f}")
        lines.append(f"  Total Returns: ${metrics.get('total_returns', 0):,.2f}")

    return "\n".join(lines)


# ─── Core API Methods ─────────────────────────────────────────────────────────


def is_available() -> bool:
    """Return True if the Gemini API key is configured."""
    return get_settings().has_api_key


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
    client = _ensure_client()
    settings = get_settings()
    user_message = sanitize_user_input(user_message)

    system_prompt = build_system_prompt()
    context_block = f"\n\n{financial_context}\n\n" if financial_context else ""

    # Build contents list for the new SDK
    from google.genai import types

    contents = []

    # Replay history (cap at MAX_HISTORY_TURNS for token efficiency)
    recent_history = chat_history[-MAX_HISTORY_TURNS:]
    for msg in recent_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    # Append current user message with context injected
    if not recent_history:
        current_text = f"{context_block}{user_message}"
    else:
        current_text = user_message

    contents.append(types.Content(role="user", parts=[types.Part(text=current_text)]))

    config = types.GenerateContentConfig(
        system_instruction=f"{system_prompt}{context_block}",
        max_output_tokens=settings.gemini_max_tokens,
        temperature=settings.gemini_temperature,
    )

    start = time.perf_counter()
    try:
        response_stream = client.models.generate_content_stream(
            model=settings.gemini_model,
            contents=contents,
            config=config,
        )
        full_text = ""
        token_in = 0
        token_out = 0
        for chunk in response_stream:
            if chunk.text:
                full_text += chunk.text
                yield chunk.text
            # Track usage from the last chunk
            if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                token_in = getattr(chunk.usage_metadata, "prompt_token_count", 0) or 0
                token_out = getattr(chunk.usage_metadata, "candidates_token_count", 0) or 0

        latency_ms = (time.perf_counter() - start) * 1000
        if token_in or token_out:
            logger.info(
                "Gemini API  |  tokens_in=%d  tokens_out=%d  latency=%dms",
                token_in,
                token_out,
                int(latency_ms),
            )
    except GeminiAPIError:
        raise
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
    client = _ensure_client()
    settings = get_settings()
    context = build_financial_context(metrics)

    from google.genai import types

    goals_text = "\n".join(
        f"- {g['name']}: ${g['target_amount']:,.2f} by {g['target_date']} (Priority: {g['priority']})"
        for g in goals
    )

    prompt = (
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

    config = types.GenerateContentConfig(
        system_instruction=build_system_prompt(),
        max_output_tokens=settings.gemini_max_tokens,
        temperature=settings.gemini_temperature,
    )

    start = time.perf_counter()
    try:
        response = _call_with_retry(
            client.models.generate_content,
            model=settings.gemini_model,
            contents=prompt,
            config=config,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        usage = getattr(response, "usage_metadata", None)
        if usage:
            logger.info(
                "Gemini API  |  tokens_in=%d  tokens_out=%d  latency=%dms",
                getattr(usage, "prompt_token_count", 0) or 0,
                getattr(usage, "candidates_token_count", 0) or 0,
                int(latency_ms),
            )
        return response.text
    except GeminiAPIError:
        raise
    except Exception as exc:
        logger.error("Gemini plan generation error: %s", exc)
        return f"⚠️ Could not generate plan: {exc}"


def analyze_spending_patterns(expense_data: dict, income: float) -> str:
    """Ask Gemini for AI-driven commentary on spending habits.

    Parameters
    ----------
    expense_data : dict
        Category -> amount mapping.
    income : float
        Monthly income for ratio context.

    Returns
    -------
    str  AI commentary text.
    """
    client = _ensure_client()
    settings = get_settings()

    from google.genai import types

    breakdown = "\n".join(
        f"  - {cat}: ${amt:,.2f} ({amt / income * 100:.1f}% of income)" if income > 0 else f"  - {cat}: ${amt:,.2f}"
        for cat, amt in expense_data.items()
    )

    prompt = (
        f"Monthly Income: ${income:,.2f}\n"
        f"Expense Breakdown:\n{breakdown}\n\n"
        "Provide a concise analysis of these spending patterns:\n"
        "1. Which categories seem high relative to income?\n"
        "2. What specific optimizations could reduce spending?\n"
        "3. Are there any concerning patterns?\n"
        "Keep the response under 300 words."
    )

    config = types.GenerateContentConfig(
        system_instruction=build_system_prompt(),
        max_output_tokens=settings.gemini_max_tokens,
        temperature=settings.gemini_temperature,
    )

    try:
        response = _call_with_retry(
            client.models.generate_content,
            model=settings.gemini_model,
            contents=prompt,
            config=config,
        )
        return response.text
    except GeminiAPIError:
        raise
    except Exception as exc:
        logger.error("Spending analysis error: %s", exc)
        return f"⚠️ Could not analyze spending: {exc}"
