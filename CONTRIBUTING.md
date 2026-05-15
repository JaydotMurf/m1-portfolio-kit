# Contributing

## Setup

```bash
git clone https://github.com/JaydotMurf/m1-portfolio-kit.git
cd m1-portfolio-kit
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
streamlit run app.py
```

## Running tests

```bash
pytest tests/
```

All tests must pass before opening a pull request. CI runs the same suite on every push.

## Ground rules

- **`core/loader.py` owns the M1 CSV format.** Raw column names (`Symbol`, `Avg. Price`, etc.) must not appear anywhere else.
- **No new packages** without updating `requirements.txt` and noting the reason in the PR.
- **Phase 1 scope only.** Features planned for Phase 2+ (multi-snapshot, benchmarks) are not in scope until Phase 1 is fully shipped.
- **No hardcoded tickers or personal holdings data** anywhere in the codebase.

## Opening a PR

1. Fork the repo and create a branch from `main`.
2. Make your changes and run `pytest tests/` locally.
3. Open a pull request — CI will run automatically.
4. Describe what you changed and why in the PR body.
