import pandas as pd
from sql_queries.sheet1 import first_sql_map
from .base import execute_queries

def remap_tab1(results: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    if "q1" not in results:
        base_key = "scatter-plot-q1" if "scatter-plot-q1" in results else None
        if base_key:
            results["q1"] = results.get(base_key, pd.DataFrame())
        else:
            # last resort: try any DataFrame that has the expected columns
            for k, df in results.items():
                cols = set(df.columns)
                if {"rgn", "outlet_category"} <= cols and (
                    {"sales_outlet"} <= cols or {"outlet_name"} <= cols
                ):
                    results["q1"] = df
                    break
            results.setdefault("q1", pd.DataFrame())
    return results

def get_tab1_results():
    """Execute SQL and normalize keys expected by Tab 1 figures."""
    return execute_queries(first_sql_map, "Tab1", remap_tab1)