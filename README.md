<h1 align="center">💰 Penny</h1>

<p align="center">
  <strong>AI-powered personal finance advisor built with Streamlit & Google Gemini.</strong><br/>
  Analyze your budget, chat with an AI advisor, and plan your financial goals.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Google%20Gemini-4285F4?style=flat-square&logo=google&logoColor=white" alt="Gemini"/>
</p>

---

## Features

- 📊 **Dashboard** — Interactive charts and a Financial Health Score
- 🤖 **AI Chat** — Conversational financial advisor powered by Gemini
- 🎯 **Goal Planner** — Track savings goals with AI-generated plans
- 📈 **Investment Projections** — Compound growth modeling
- 💳 **Debt Analysis** — DTI ratio & payoff timelines

---

## Quick Start

```bash
# Clone & setup
git clone https://github.com/nayiswftw/penny.git
cd penny
python -m venv .venv && .venv\Scripts\activate   # or source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.template .env
# Edit .env and add your GEMINI_API_KEY (get one at https://aistudio.google.com)

# Run
streamlit run app.py
```

> Also works with **GitHub Codespaces** — just create a codespace and set `GEMINI_API_KEY` as a secret.

---

## Configuration

Set these in your `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | **Required.** Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-pro` | Model to use |
| `GEMINI_TEMPERATURE` | `0.3` | Response creativity (lower = more factual) |
| `DATA_SOURCE` | `user_input` | Data source mode |

See [`.env.template`](.env.template) for all available options.

---

## Disclaimer

Penny provides **general financial guidance** only — not professional financial, tax, or legal advice.

---

<p align="center">
  Built with ❤️ using <a href="https://streamlit.io">Streamlit</a> & <a href="https://ai.google.dev">Google Gemini</a>
</p>
