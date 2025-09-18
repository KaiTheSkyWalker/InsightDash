from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.colors import category_color_map as get_category_color_map


KPI_DISPLAY = [
    ("new_car_reg_pct", "New Car Reg"),
    ("gear_up_ach_pct", "Gear Up"),
    ("ins_renew_1st_pct", "Ins Renew 1st"),
    ("ins_renew_overall_pct", "Ins Renew Overall"),
    ("pov_pct", "POV"),
    ("intake_pct", "Intake"),
    ("revenue_pct", "Revenue"),
    ("parts_pct", "Parts"),
    ("lubricant_pct", "Lubricant"),
    ("cs_sales_pct", "CS Sales"),
    ("nps_sales_pct", "NPS Sales"),
    ("eappointment_pct", "eAppointment"),
    ("qpi_pct", "QPI"),
    ("cs_service_pct", "CS Service"),
]


def _apply_filters(df: pd.DataFrame, f: Dict) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    # Normalize outlet name
    if "outlet_name" not in out.columns and "sales_outlet" in out.columns:
        out = out.rename(columns={"sales_outlet": "outlet_name"})
    if f.get("regions") and "rgn" in out.columns:
        out = out[out["rgn"].isin(f["regions"])]
    if f.get("outlet_categories") and "outlet_category" in out.columns:
        out = out[out["outlet_category"].isin(f["outlet_categories"])]
    if f.get("outlet_types") and "outlet_type" in out.columns:
        out = out[out["outlet_type"].isin(f["outlet_types"])]
    st = (f.get("search_text") or "").strip().lower()
    if st and "outlet_name" in out.columns:
        try:
            out = out[out["outlet_name"].str.lower().str.contains(st, na=False)]
        except Exception:
            pass
    return out


def _normalize_cols(d: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to KPI *_pct names for downstream use (radars)."""
    if d is None or d.empty:
        return d
    out = d.copy()
    rename_map = {}
    for k, _ in KPI_DISPLAY:
        ak = f"avg_{k.replace('_pct', '')}"
        if ak in out.columns:
            rename_map[ak] = k
    for c in list(out.columns):
        if c.startswith("avg_") and c.endswith("_pct"):
            rename_map[c] = c.replace("avg_", "")
    if rename_map:
        out = out.rename(columns=rename_map)
    return out


def get_filtered_frames_simple(
    data: Dict[str, pd.DataFrame], filters: Dict
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return base q1 (detail) and radar-source table as q2 after applying filters.

    q1: filtered detailed table (used for diverging bar inputs)
    q2: filtered + normalized table used by the radar charts (avg KPI pct columns by outlet_type)
    q3/q4: currently unused
    """
    q1 = _apply_filters(data.get("q1", pd.DataFrame()), filters)
    after_tbl = _normalize_cols(q1)
    # Keep only B/C/D unless a single category explicitly selected
    sel_cats = list(filters.get("outlet_categories") or [])
    if len(sel_cats) == 1:
        if "outlet_category" in after_tbl.columns:
            after_tbl = after_tbl[after_tbl["outlet_category"] == sel_cats[0]]
    else:
        if "outlet_category" in after_tbl.columns:
            after_tbl = after_tbl[after_tbl["outlet_category"].isin(["B", "C", "D"])]
    return q1, after_tbl, pd.DataFrame(), pd.DataFrame()


# merged_for_chart2 was previously unused; removed in cleanup.


def build_tab3_figures(
    data: Dict[str, pd.DataFrame],
    filters: Dict,
    outlet_color_map: Dict[str, str] | None = None,
    tier_colors: Dict[str, str] | None = None,
    all_outlet_categories: List[str] | None = None,
    labels: Dict[str, str] | None = None,
    scatter_color_map: Dict[str, str] | None = None,
) -> Tuple[go.Figure, go.Figure, go.Figure, go.Figure, go.Figure]:
    """Tab 3 — Category and Type Diagnostics per spec.

    - fig1: Diverging bar chart of average (KPI_pct - 100) by outlet_category (B/C/D) across KPIs.
    - fig2: Radar chart of average KPI profiles by outlet_type for the selected category.
    - fig3: removed per new spec (two charts only).
    """
    df0 = data.get("q1", pd.DataFrame()).copy()
    df = _apply_filters(df0, filters)

    # 1) Diverging bar chart (grouped by category B/C/D)
    fig1 = go.Figure()
    if not df.empty:
        # Compute avg gap from target 100 for each KPI by category
        rows = []
        cats = ["B", "C", "D"]
        for col, disp in KPI_DISPLAY:
            if col not in df.columns:
                continue
            g = (
                df[df["outlet_category"].isin(cats)]
                .groupby("outlet_category")[col]
                .mean()
                .reindex(cats)
            )
            for cat, val in g.items():
                if pd.notna(val):
                    rows.append(
                        {
                            "outlet_category": cat,
                            "kpi": disp,
                            "gap_value": float(val) - 100.0,
                            "kpi_col": col,
                        }
                    )
        if rows:
            plot = pd.DataFrame(rows)
            fig1 = px.bar(
                plot,
                x="gap_value",
                y="kpi",
                color="outlet_category",
                barmode="group",
                orientation="h",
                title=(labels or {}).get(
                    "t3-graph-1", "What's Holding Back B, C, & D Outlets?"
                ),
                color_discrete_map=get_category_color_map(),
                custom_data=["outlet_category", "kpi_col", "kpi"],
            )
            fig1.add_vline(x=0, line_color="#9CA3AF")
            # Increase vertical spacing between KPI rows
            fig1.update_layout(
                uirevision="t3", margin=dict(t=24), bargap=0.32, bargroupgap=0.22
            )
    if not fig1.data:
        fig1.add_annotation(
            text="No data available (need KPI % columns and outlet_category)",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color="#6b7280"),
        )
        fig1.update_layout(
            title=(labels or {}).get(
                "t3-graph-1", "What's Holding Back B, C, & D Outlets?"
            ),
            margin=dict(t=24),
        )

    # 2) Radar chart: Average Performance Profile by Outlet Type within selected category

    df_after = df.copy()

    # Harmonize columns to KPI names
    after_tbl = _normalize_cols(df_after)
    # Determine scope: selected category vs all B/C/D
    sel_cats = list(filters.get("outlet_categories") or [])
    if len(sel_cats) == 1 and not after_tbl.empty:
        sel = sel_cats[0]
        if "outlet_category" in after_tbl.columns:
            after_tbl = after_tbl[after_tbl["outlet_category"] == sel]
        title_suffix = f"— Category {sel}"
    else:
        if "outlet_category" in after_tbl.columns:
            after_tbl = after_tbl[after_tbl["outlet_category"].isin(["B", "C", "D"])]
        title_suffix = "— All B/C/D"

    cols_after = [k for k, _ in KPI_DISPLAY if k in after_tbl.columns]
    name_map = dict(KPI_DISPLAY)

    def radar_for_type(df_src: pd.DataFrame, typ: str) -> go.Figure:
        fig = go.Figure()
        if (
            df_src is None
            or df_src.empty
            or not cols_after
            or "outlet_type" not in df_src.columns
        ):
            fig.update_layout(
                title=f"{typ} — Average Performance Profile {title_suffix}",
                margin=dict(t=24),
            )
            fig.add_annotation(
                text="No data",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(color="#6b7280"),
            )
            return fig
        sub = df_src[df_src["outlet_type"] == typ].copy()
        # Enforce KPI scope by outlet type: set out-of-scope KPIs to 0
        sales_kpis = {
            "new_car_reg_pct",
            "gear_up_ach_pct",
            "ins_renew_1st_pct",
            "ins_renew_overall_pct",
            "pov_pct",
            "nps_sales_pct",
            "cs_sales_pct",
        }
        service_kpis = {
            "intake_pct",
            "revenue_pct",
            "parts_pct",
            "lubricant_pct",
            "eappointment_pct",
            "qpi_pct",
            "cs_service_pct",
        }
        if typ == "1S":
            for col in service_kpis.intersection(sub.columns):
                sub[col] = 0
        if typ == "2S":
            for col in sales_kpis.intersection(sub.columns):
                sub[col] = 0
        if sub.empty:
            fig.update_layout(
                title=f"{typ} — Average Performance Profile {title_suffix}",
                margin=dict(t=24),
            )
            fig.add_annotation(
                text="No data for this type",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(color="#6b7280"),
            )
            return fig
        mv = sub[cols_after].mean(numeric_only=True)
        plot = pd.DataFrame({"kpi": mv.index, "value": mv.values})
        plot["kpi_disp"] = plot["kpi"].map(name_map).fillna(plot["kpi"])
        fig = px.line_polar(
            plot,
            r="value",
            theta="kpi_disp",
            line_close=True,
            title=f"{typ} — Average Performance Profile {title_suffix}",
        )
        fig.update_traces(fill="toself", opacity=0.55, showlegend=False)
        try:
            vmax = float(plot["value"].max()) if len(plot["value"]) else 0.0
        except Exception:
            vmax = 0.0
        if vmax <= 0:
            vmax = 1.0
        # Add 10% headroom and round to nearest 5
        import math

        upper = max(1.0, math.ceil((vmax * 1.1) / 5.0) * 5.0)
        fig.update_layout(
            uirevision="t3",
            margin=dict(t=24),
            polar=dict(radialaxis=dict(range=[0, upper], showline=True)),
        )
        return fig

    fig_1s = radar_for_type(after_tbl, "1S")
    fig_2s = radar_for_type(after_tbl, "2S")
    fig_1p2s = radar_for_type(after_tbl, "1+2S")
    fig_3s = radar_for_type(after_tbl, "3S")

    # Return bar + four radars
    return fig1, fig_1s, fig_2s, fig_1p2s, fig_3s
