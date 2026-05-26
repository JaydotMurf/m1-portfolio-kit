"""
cli.py
------
Entry point for the `m1kit` command installed by pip.
Delegates to `streamlit run app.py` so the app runs correctly
without importing app.py as a module (which would run top-level Streamlit code).
"""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    app = Path(__file__).with_name("app.py")
    sys.exit(subprocess.call(["streamlit", "run", str(app)] + sys.argv[1:]))
