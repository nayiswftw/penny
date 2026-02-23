"""User-supplied financial data validation."""

from __future__ import annotations


def validate_financial_inputs(data: dict) -> list[str]:
    """Validate user-supplied financial data.

    Returns a list of human-readable error messages (empty if valid).
    """
    errors: list[str] = []

    income = data.get("income")
    if income is None:
        errors.append("Monthly income is required.")
    elif not isinstance(income, (int, float)):
        errors.append("Income must be a number.")
    elif income < 0:
        errors.append("Income cannot be negative.")

    expenses = data.get("expenses", {})
    if not expenses or all(v == 0 for v in expenses.values()):
        errors.append("At least one expense category must have a value greater than zero.")
    for cat, val in expenses.items():
        if not isinstance(val, (int, float)):
            errors.append(f"Expense '{cat}' must be a number.")
        elif val < 0:
            errors.append(f"Expense '{cat}' cannot be negative.")

    for debt in data.get("debts", []):
        rate = debt.get("interest_rate", 0)
        if rate < 0.1 or rate > 30:
            errors.append(
                f"Interest rate {rate}% for '{debt.get('name', 'debt')}' "
                "should be between 0.1% and 30%."
            )

    return errors
