from typing import Dict, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app_tabs.tab3.figures import get_filtered_frames_simple as t3_get_filtered_frames, KPI_DISPLAY


def _avg_by_category(df: pd.DataFrame, kpi_col: str) -> pd.Series:
    if df is None or df.empty or kpi_col not in df.columns:
        return pd.Series(dtype=float)
    ok = df.dropna(subset=["outlet_category", kpi_col])
    if ok.empty:
        return pd.Series(dtype=float)
    return ok.groupby("outlet_category")[kpi_col].mean().sort_index()


def build_compare_figures(
    month_data: Dict[str, Dict[str, pd.DataFrame]],
    filters: Dict,
    kpi_col: str,
) -> Tuple[go.Figure, go.Figure]:
    """Return a side-by-side bar (March vs May) and a summary table.

    month_data: {"March": {"q1": df, ...}, "May": {...}}
    filters: global filters from filter-store
    kpi_col: selected KPI column (e.g., 'revenue_pct')
    """
    # Prepare filtered detailed frames for each month
    series_by_month: Dict[str, pd.Series] = {}
    for mlabel, data in month_data.items():
        q1, _aft, _d3, _d4 = t3_get_filtered_frames(data or {}, filters or {})
        series_by_month[mlabel] = _avg_by_category(q1, kpi_col)

    # Union all categories present
    all_cats = sorted(set().union(*[set(s.index) for s in series_by_month.values() if not s.empty]))

    # Build long-form dataframe for px.bar
    rows = []
    for mlabel, s in series_by_month.items():
        for cat in all_cats:
            val = float(s.get(cat)) if cat in s.index else None
            if val is not None:
                rows.append({"Month": mlabel, "Category": cat, "Value": val})
    df_plot = pd.DataFrame(rows)

    # Bar chart
    if df_plot.empty:
        fig_bar = go.Figure()
        fig_bar.add_annotation(
            text="No data available for comparison",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color="#6b7280"),
        )
        fig_bar.update_layout(title="Month Comparison", margin=dict(t=24))
    else:
        disp_map = dict(KPI_DISPLAY)
        title = f"{disp_map.get(kpi_col, kpi_col)} — March vs May"
        fig_bar = px.bar(
            df_plot,
            x="Category",
            y="Value",
            color="Month",
            barmode="group",
            title=title,
        )
        fig_bar.update_layout(margin=dict(t=24))

    # Table figure (Category, March, May, Diff)
    # Build wide table
    def _val(s: pd.Series, cat: str) -> float | None:
        try:
            v = s.get(cat)
            return float(v) if v is not None else None
        except Exception:
            return None

    march = series_by_month.get("March", pd.Series(dtype=float))
    may = series_by_month.get("May", pd.Series(dtype=float))
    tab_rows = []
    for cat in all_cats:
        m1 = _val(march, cat)
        m2 = _val(may, cat)
        diff = (m2 - m1) if (m1 is not None and m2 is not None) else None
        tab_rows.append([cat, m1, m2, diff])

    if not tab_rows:
        fig_tbl = go.Figure()
        fig_tbl.update_layout(margin=dict(t=10))
    else:
        cols = ["Category", "March Avg", "May Avg", "Δ (May - March)"]
        col_vals = list(map(list, zip(*tab_rows)))  # transpose
        fig_tbl = go.Figure(
            data=[
                go.Table(
                    header=dict(values=cols, fill_color="#f3f4f6", align="left"),
                    cells=dict(values=col_vals, align="left"),
                )
            ]
        )
        fig_tbl.update_layout(margin=dict(t=10))

    return fig_bar, fig_tbl

