import os
import sys
import pandas as pd

# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.df_summary import category_mix_by_month


def build_sample():
    # Simulate outlet-level rows for two months with categories
    march = pd.DataFrame(
        {
            "Month": ["March"] * 10,
            "outlet_category": ["A", "A", "A", "A", "A", "B", "B", "C", "D", "D"],
        }
    )
    # May has fewer A proportionally
    may = pd.DataFrame(
        {
            "Month": ["May"] * 12,
            "outlet_category": [
                "A",
                "A",
                "B",
                "B",
                "B",
                "C",
                "C",
                "C",
                "D",
                "D",
                "D",
                "D",
            ],
        }
    )
    return pd.concat([march, may], ignore_index=True)


def main():
    df = build_sample()
    mix = category_mix_by_month(df)
    a_march = (
        mix[(mix["Month"] == "March") & (mix["category"] == "A")]["pct"].iloc[0]
        if not mix.empty
        else None
    )
    a_may = (
        mix[(mix["Month"] == "May") & (mix["category"] == "A")]["pct"].iloc[0]
        if not mix.empty
        else None
    )
    print("A% March:", round(a_march, 2))
    print("A% May:", round(a_may, 2))
    assert a_march is not None and a_may is not None
    assert a_march > a_may, "Expected March A% > May A%"
    print("OK: March has higher A% than May")


if __name__ == "__main__":
    main()
