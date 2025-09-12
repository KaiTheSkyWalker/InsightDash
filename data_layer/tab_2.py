import pandas as pd
from sql_queries.sheet2 import second_sql_map
from .base import execute_queries

def remap_tab2(results: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    if "q1" not in results:
        base_key = "dynamic-scatter-plot" if "dynamic-scatter-plot" in results else None
        if base_key:
            results["q1"] = results.get(base_key, pd.DataFrame())
        else:
            # Fallback: pick any with KPI % columns
            for k, df in results.items():
                cols = set(df.columns)
                if {"rgn", "outlet_category"} <= cols and (
                    {"cs_sales_pct", "new_car_reg_pct"} & cols
                ):
                    results["q1"] = df
                    break
            results.setdefault("q1", pd.DataFrame())
    return results

def get_tab2_results():
    """Execute SQL for Tab 2 and normalize keys."""
    return execute_queries(second_sql_map, "Tab2", remap_tab2)