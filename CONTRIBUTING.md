# Contributing

## Setup

### From source

```bash
git clone https://github.com/JaydotMurf/m1-portfolio-kit.git
cd m1-portfolio-kit
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
streamlit run app.py
```

To enable the optional benchmark overlay (SPY/QQQ on the Timeline tab):

```bash
pip install ".[benchmarks]"
```

### Docker

```bash
docker build -t m1-portfolio-kit .
docker run -p 8501:8501 m1-portfolio-kit
```

OrbStack is the recommended Docker runtime on Mac (lighter than Docker Desktop):
`brew install --cask orbstack`

## Running tests

```bash
pytest tests/
```

All tests must pass before opening a pull request. CI runs the same suite on every push.

## Ground rules

- **`core/loader.py` owns the M1 CSV format.** Raw column names (`Symbol`, `Avg. Price`, etc.) must not appear anywhere else.
- **No new runtime packages** without updating `pyproject.toml` (and `requirements.txt` for Docker/CI compatibility) and noting the reason in the PR.
- **Optional dependencies** (e.g. `yfinance`) go in `requirements-optional.txt` and the `[project.optional-dependencies]` section of `pyproject.toml`. They must be guarded with `try/except ImportError` and never imported unconditionally.
- **No hardcoded tickers or personal holdings data** anywhere in the codebase. Tests use synthetic CSV fixtures only.
- **All tests must pass** before committing. Do not open a PR with failing tests.

## Opening a PR

1. Fork the repo and create a branch from `main`.
2. Make your changes and run `pytest tests/` locally.
3. Open a pull request — CI will run automatically.
4. Describe what you changed and why in the PR body.
