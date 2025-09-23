from __future__ import annotations

import calendar
from typing import Dict, Tuple, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app_tabs.tab3.figures import (
    get_filtered_frames_simple as t3_get_filtered_frames,
    KPI_DISPLAY,
)


MONTH_NAME_LOOKUP = {
    name.lower(): idx for idx, name in enumerate(calendar.month_name) if name
}
MONTH_ABBR_LOOKUP = {
    name.lower(): idx for idx, name in enumerate(calendar.month_abbr) if name
}


def _avg_by_category(df: pd.DataFrame, kpi_col: str) -> pd.Series:
    if df is None or df.empty or kpi_col not in df.columns:
        return pd.Series(dtype=float)
    ok = df.dropna(subset=["outlet_category", kpi_col])
    if ok.empty:
        return pd.Series(dtype=float)
    return ok.groupby("outlet_category")[kpi_col].mean().sort_index()


def _ordered_month_labels(labels: List[str]) -> List[str]:
    if not labels:
        return []

    ordered: List[tuple[tuple[int, int, int], str]] = []
    for pos, raw in enumerate(labels):
        label = str(raw).strip()
        tokens = label.replace("-", " ").replace("/", " ").split()
        month_num: int | None = None
        year: int | None = None

        for token in tokens:
            key = token.lower()
            if key in MONTH_NAME_LOOKUP:
                month_num = MONTH_NAME_LOOKUP[key]
                continue
            if key in MONTH_ABBR_LOOKUP:
                month_num = MONTH_ABBR_LOOKUP[key]
                continue
            if token.isdigit() and len(token) == 4:
                year = int(token)

        if month_num is None:
            try:
                parsed = pd.to_datetime(label, errors="coerce")
            except Exception:
                parsed = pd.NaT
            if pd.notna(parsed):
                month_num = int(parsed.month)
                year = int(parsed.year)

        if month_num is None:
            month_num = 99
        if year is None:
            year = 0

        ordered.append(((year, month_num, pos), label))

    ordered.sort(key=lambda x: x[0])
    return [label for _, label in ordered]


def _series_mean(df: pd.DataFrame, col: str) -> float | None:
    if df is None or df.empty or col not in df.columns:
        return None
    try:
        return float(df[col].dropna().mean())
    except Exception:
        return None


def _round_value(val: float | None, ndigits: int = 2) -> float | None:
    if val is None:
        return None
    try:
        return round(float(val), ndigits)
    except Exception:
        return val


def build_compare_figures(
    month_data: Dict[str, Dict[str, pd.DataFrame]],
    filters: Dict,
    kpi_col: str,
) -> Tuple[go.Figure, go.Figure]:
    """Build a time-series trend chart and summary table for the Compare tab."""

    filters = filters or {}
    ordered_months = _ordered_month_labels(list(month_data.keys()))
    series_by_month: Dict[str, pd.Series] = {}
    overall_by_month: Dict[str, float | None] = {}

    for mlabel in ordered_months:
        data = month_data.get(mlabel) or {}
        q1, _aft, _d3, _d4 = t3_get_filtered_frames(data, filters)
        series_by_month[mlabel] = _avg_by_category(q1, kpi_col)
        overall_by_month[mlabel] = _series_mean(q1, kpi_col)

    # Collect category labels and ensure deterministic ordering
    category_sets = [set(s.index) for s in series_by_month.values() if isinstance(s, pd.Series)]
    cat_labels = sorted(set().union(*category_sets)) if category_sets else []

    has_overall = any(v is not None for v in overall_by_month.values())
    ordered_categories: List[str] = ["Overall"] if has_overall else []
    ordered_categories.extend(cat_labels)

    # Build long-form dataframe for the line chart
    rows: List[dict] = []
    month_order_map = {label: idx for idx, label in enumerate(ordered_months)}
    for mlabel in ordered_months:
        s = series_by_month.get(mlabel, pd.Series(dtype=float))
        if has_overall:
            overall_val = overall_by_month.get(mlabel)
            if overall_val is not None:
                rows.append(
                    {
                        "Month": mlabel,
                        "Category": "Overall",
                        "Value": float(overall_val),
                        "_month_order": month_order_map[mlabel],
                    }
                )
        for cat in cat_labels:
            val = s.get(cat) if cat in s.index else None
            if pd.notna(val):
                rows.append(
                    {
                        "Month": mlabel,
                        "Category": cat,
                        "Value": float(val),
                        "_month_order": month_order_map[mlabel],
                    }
                )

    df_plot = pd.DataFrame(rows)

    if df_plot.empty:
        fig_line = go.Figure()
        fig_line.add_annotation(
            text="No data available for the selected KPI",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color="#6b7280"),
        )
        fig_line.update_layout(title="Month-over-Month Trend", margin=dict(t=24))
    else:
        df_plot = df_plot.sort_values(["_month_order", "Category"])
        disp_map = dict(KPI_DISPLAY)
        title = f"{disp_map.get(kpi_col, kpi_col)} — Monthly Trend"
        fig_line = px.line(
            df_plot,
            x="Month",
            y="Value",
            color="Category",
            markers=True,
            category_orders={
                "Month": ordered_months,
                "Category": ordered_categories,
            },
            title=title,
        )
        fig_line.update_layout(margin=dict(t=32))
        fig_line.update_traces(mode="lines+markers")

    # Build summary table (category vs month with delta)
    table_rows: List[List[float | None | str]] = []
    for cat in ordered_categories:
        month_vals: List[float | None] = []
        for mlabel in ordered_months:
            if cat == "Overall":
                month_vals.append(overall_by_month.get(mlabel))
            else:
                s = series_by_month.get(mlabel, pd.Series(dtype=float))
                val = s.get(cat) if cat in s.index else None
                month_vals.append(float(val) if pd.notna(val) else None)

        first_val = next((v for v in month_vals if v is not None), None)
        last_val = next((v for v in reversed(month_vals) if v is not None), None)
        delta = (last_val - first_val) if (first_val is not None and last_val is not None) else None

        rounded_vals = [_round_value(v) for v in month_vals]
        table_rows.append([cat, *rounded_vals, _round_value(delta)])

    if not table_rows:
        fig_tbl = go.Figure()
        fig_tbl.update_layout(margin=dict(t=10))
    else:
        headers = ["Category", *ordered_months, "Δ (Last - First)"]
        col_values = list(map(list, zip(*table_rows)))
        fig_tbl = go.Figure(
            data=[
                go.Table(
                    header=dict(values=headers, fill_color="#f3f4f6", align="left"),
                    cells=dict(values=col_values, align="left"),
                )
            ]
        )
        fig_tbl.update_layout(margin=dict(t=10))

    return fig_line, fig_tbl

