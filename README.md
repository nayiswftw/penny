<p align="center">
  <img src="assets/logo.png" alt="Penny logo" width="80" />
  <br/>
  <strong style="font-size:2em;">Penny</strong>
</p>

<h3 align="center">AI-Powered Personal Finance Advisor</h3>

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#tech-stack">Tech Stack</a> ·
  <a href="#getting-started">Getting Started</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#project-structure">Project Structure</a> ·
  <a href="#contributing">Contributing</a> ·
  <a href="#license">License</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/streamlit-1.28+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/gemini-AI-8E75B2?style=flat-square&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square" />
</p>

---

**Penny** is an interactive, AI-powered financial advisor that helps you analyze your budget, track debt, project investments, and get personalized guidance — all from a beautiful dark-mode dashboard.

Enter your income, expenses, and debts in the sidebar, hit **Analyze**, and Penny crunches the numbers instantly. Need deeper advice? Ask the built-in **AI Advisor** (powered by Google Gemini) anything about your finances.

## Features

| Category | What You Get |
|---|---|
| **Budget Analysis** | Automatic expense-to-income ratios, surplus calculation, and savings potential |
| **Savings Scoring** | Savings-rate tracking benchmarked against the 20 % rule |
| **Debt Metrics** | Debt-to-income ratio, per-debt payoff timelines with amortisation math |
| **Investment Projections** | Compound-interest growth projections with monthly contributions over custom time horizons |
| **Financial Health Score** | Composite 0–100 score weighted across savings, debt, budget, and investments |
| **AI Chat Advisor** | Multi-turn streamed conversation with Gemini for personalised financial guidance |
| **Goal Planning** | Set financial goals and let AI generate an actionable plan to reach them |
| **Interactive Charts** | Expense donut, income vs expense bars, investment growth area, debt payoff timeline, health gauge, budget waterfall — all in Plotly |
| **CSV Export** | Download your analysis results for offline use |

## Tech Stack

- **Frontend / UI** — [Streamlit](https://streamlit.io) with a custom dark-mode glassmorphism theme
- **AI Engine** — [Google Gemini](https://ai.google.dev/) (`google-genai`) with streaming, retry logic, and configurable model parameters
- **Data & Analysis** — [Pandas](https://pandas.pydata.org/) + [NumPy](https://numpy.org/)
- **Visualization** — [Plotly](https://plotly.com/python/) (themed, responsive charts)
- **Config & Validation** — [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) with `.env` support
- **Code Quality** — [Ruff](https://docs.astral.sh/ruff/) (lint + format), [Mypy](https://mypy-lang.org/), [pre-commit](https://pre-commit.com/)
- **Testing** — [pytest](https://docs.pytest.org/) with coverage

## Getting Started

### Prerequisites

- **Python 3.9+**
- A **Google Gemini API key** — get one free at [aistudio.google.com](https://aistudio.google.com/)

### Installation

```bash
# Clone the repo
git clone https://github.com/<your-username>/penny.git
cd penny

# Create & activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy the example env file and fill in your API key:

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```dotenv
GEMINI_API_KEY=your_google_gemini_api_key_here
```

<details>
<summary>All available environment variables</summary>

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | **Required.** Your Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-pro` | Gemini model to use |
| `GEMINI_MAX_TOKENS` | `8192` | Max output tokens per request |
| `GEMINI_TEMPERATURE` | `0.3` | Creativity (0 = deterministic, 2 = very creative) |
| `APP_TITLE` | `AI Financial Advisor` | Title shown in the browser tab |
| `APP_ENV` | `development` | `development` or `production` |
| `DATA_SOURCE` | `user_input` | Data source mode |
| `ALPHA_VANTAGE_KEY` | — | Optional Alpha Vantage API key |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `CACHE_TTL_SECONDS` | `300` | Cache time-to-live in seconds |

</details>

## Usage

```bash
streamlit run src/penny/app.py
```

The app opens at **http://localhost:8501** by default.

### Quick Workflow

1. **Enter your data** — Fill in monthly income, expense categories, and any debts in the sidebar.
2. **Analyze** — Click the analyze button to compute budget breakdown, savings rate, debt metrics, investment projections, and your health score.
3. **Explore the Dashboard** — Browse interactive charts and metric cards.
4. **Chat with the AI Advisor** — Switch to the *AI Advisor* tab and ask follow-up questions about your finances.
5. **Set Goals** — Head to the *Financial Goals* tab to define targets and generate an AI-powered action plan.

## Project Structure

```
penny/
├── .streamlit/
│   └── config.toml            # Streamlit theme & server settings
├── assets/
│   └── logo.png               # App logo / favicon
├── src/
│   └── penny/                 # Main Python package
│       ├── app.py             # Application entrypoint
│       ├── config.py          # Pydantic Settings + logging setup
│       ├── finance_analysis.py# Core financial computation engine
│       ├── ai_advisor.py      # Gemini AI integration (streaming, retries)
│       ├── visualization.py   # Plotly chart library
│       ├── exceptions.py      # Custom exception hierarchy
│       ├── views/
│       │   ├── sidebar.py     # Data entry sidebar
│       │   ├── dashboard.py   # Metrics + charts dashboard
│       │   ├── chat.py        # AI chat interface
│       │   └── goals.py       # Financial goal tracker
│       └── utils/
│           ├── validation.py  # Input validation
│           ├── export.py      # CSV export helpers
│           ├── cache.py       # Caching utilities
│           ├── formatting.py  # Number / currency formatting
│           └── sanitize.py    # Input sanitisation
├── tests/
│   ├── conftest.py            # Shared fixtures
│   ├── test_finance_analysis.py
│   ├── test_ai_advisor.py
│   └── test_utils.py
├── .env.example               # Sample environment config
├── .pre-commit-config.yaml    # Ruff, Mypy, pre-commit hooks
├── pyproject.toml             # Project metadata, tooling config
└── requirements.txt           # Runtime dependencies
```

## Development

### Install dev dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Lint & format

```bash
ruff check src/ tests/
ruff format src/ tests/
```

### Type-check

```bash
mypy src/
```

### Pre-commit hooks

```bash
pre-commit install      # one-time setup
pre-commit run --all    # manual run
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

Make sure `ruff`, `mypy`, and `pytest` pass before submitting.

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<p align="center">
  Built with ☕ and curiosity &nbsp;·&nbsp; Powered by <a href="https://ai.google.dev/">Google Gemini</a>
</p>
