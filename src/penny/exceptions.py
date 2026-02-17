"""
exceptions.py — Custom Exception Hierarchy
───────────────────────────────────────────
Centralised exception types for clear error handling across all modules.
"""

from __future__ import annotations


class PennyError(Exception):
    """Base exception for all Penny application errors."""


class ConfigurationError(PennyError):
    """Raised when a required configuration value is missing or invalid."""


class GeminiAPIError(PennyError):
    """Raised when a Gemini API call fails."""


class GeminiRateLimitError(GeminiAPIError):
    """Raised when the Gemini API rate limit is exceeded."""


class GeminiTimeoutError(GeminiAPIError):
    """Raised when a Gemini API call exceeds the timeout threshold."""


class ValidationError(PennyError):
    """Raised when user-supplied financial data fails validation."""


class ExportError(PennyError):
    """Raised when CSV or report export fails."""
