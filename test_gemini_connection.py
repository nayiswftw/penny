"""
Gemini API Connectivity Smoke Test
───────────────────────────────────
Validates that the configured API key can authenticate and receive
a response from the Google Gemini model.

Usage:
    python test_gemini_connection.py
"""

import sys
import time
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

    if not api_key or api_key == "your_google_gemini_api_key_here":
        print("❌  GEMINI_API_KEY is missing or still set to the placeholder value.")
        print("   Copy .env.template → .env and add your real API key.")
        sys.exit(1)

    try:
        import google.generativeai as genai
    except ImportError:
        print("❌  google-generativeai package not installed. Run:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    print(f"🔌  Testing connection to model '{model_name}' …")

    start = time.perf_counter()
    try:
        response = model.generate_content("Respond with OK if you can read this.")
        latency_ms = (time.perf_counter() - start) * 1000
    except Exception as exc:
        print(f"❌  API call failed: {exc}")
        sys.exit(1)

    text = response.text.strip() if response.text else ""
    if not text:
        print("❌  Received an empty response from the API.")
        sys.exit(1)

    # ── Report ────────────────────────────────────────────────
    print(f"✅  Connection successful!")
    print(f"    Model       : {model_name}")
    print(f"    Response    : {text[:120]}")
    print(f"    Latency     : {latency_ms:.0f} ms")

    usage = getattr(response, "usage_metadata", None)
    if usage:
        print(f"    Tokens in   : {getattr(usage, 'prompt_token_count', 'N/A')}")
        print(f"    Tokens out  : {getattr(usage, 'candidates_token_count', 'N/A')}")

    sys.exit(0)


if __name__ == "__main__":
    main()
