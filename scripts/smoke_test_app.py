import os
import sys
from pathlib import Path

# Force offline mode to avoid DB/LLM calls and server run
os.environ["DASH_OFFLINE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as app_module


def main():
    # Minimal empty datasets
    t1 = {}
    t2 = {}
    t3 = {}
    monthly = {}
    dash_app = app_module.create_dashboard(t1, t2, t3, monthly)
    # Access layout to ensure it builds
    _ = dash_app.layout
    print("SMOKE_OK")


if __name__ == "__main__":
    main()
