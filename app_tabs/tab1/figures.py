from typing import Tuple, List, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.colors import brand_palette
from utils.colors import category_color_map as get_category_color_map
from utils.colors import color_map_from_list


def get_filtered_frames(
    data_dict: Dict[str, pd.DataFrame], filters: Dict
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Single-source Tab 1: derive region aggregates from detailed q1 and return outlet detail for q4/q5."""
    base = data_dict.get("q1", pd.DataFrame()).copy()

    # normalize outlet name column
    if "outlet_name" not in base.columns and "sales_outlet" in base.columns:
        base = base.rename(columns={"sales_outlet": "outlet_name"})

    regions = filters.get("regions") or []
    cats = filters.get("outlet_categories") or []
    types = filters.get("outlet_types") or []
    search = (filters.get("search_text") or "").strip().lower()

    if regions and "rgn" in base.columns:
        base = base[base["rgn"].isin(regions)]
    if cats and "outlet_category" in base.columns:
        base = base[base["outlet_category"].isin(cats)]
    if types and "outlet_type" in base.columns:
        base = base[base["outlet_type"].isin(types)]
    if search and "outlet_name" in base.columns:
        try:
            base = base[base["outlet_name"].str.lower().str.contains(search, na=False)]
        except Exception:
            pass

    # region aggregates
    if base.empty or "rgn" not in base.columns:
        agg = pd.DataFrame()
    else:
        agg = (
            base.groupby("rgn", dropna=False)
            .agg(
                avg_total_score=("total_score", "mean"),
                avg_rate_performance=("rate_performance", "mean"),
                avg_rate_quality=("rate_quality", "mean"),
                cat_a=("outlet_category", lambda s: (s == "A").sum()),
                cat_b=("outlet_category", lambda s: (s == "B").sum()),
                cat_c=("outlet_category", lambda s: (s == "C").sum()),
                cat_d=("outlet_category", lambda s: (s == "D").sum()),
            )
            .reset_index()
        )

    # Build category mix by region (100%) for q2
    df_q2 = pd.DataFrame()
    try:
        if not agg.empty:
            rcol = "rgn" if "rgn" in agg.columns else None
            cat_cols = [
                c for c in ["cat_a", "cat_b", "cat_c", "cat_d"] if c in agg.columns
            ]
            if rcol and cat_cols:
                mix = agg[[rcol] + cat_cols].copy()
                mix = mix.melt(id_vars=[rcol], var_name="category", value_name="count")
                # Friendly A/B/C/D labels
                try:
                    mix["category"] = (
                        mix["category"].str.extract(r"cat_([abcd])")[0].str.upper()
                    )
                except Exception:
                    pass
                totals = mix.groupby(rcol, dropna=False)["count"].transform("sum")
                mix["pct"] = (mix["count"] / totals) * 100.0
                df_q2 = mix
    except Exception:
        df_q2 = pd.DataFrame()

    # Use detailed base for q4/q5
    return agg, df_q2, pd.DataFrame(), base.copy(), base.copy()


def build_tab1_figures(
    data_dict: Dict[str, pd.DataFrame],
    filters: Dict,
    all_outlet_categories: List[str],
    all_regions: List[str],
    outlet_color_map: Dict[str, str],
    region_color_map: Dict[str, str],
    base_palette: List[str],
    GRAPH_LABELS: Dict[str, str],
):
    """Return Tab 1 figures with:
    - q1: Avg Total Score by Region
    - q2: Category Mix by Region (100%)
    - q3: Performance vs Quality by Region
    - q4: Top Outlets by Score
    - q5: Bottom Outlets by Score
    - q6: Outlet Count by Category
    """
    df_q1, _df2, _df3, df_q4, df_q5 = get_filtered_frames(data_dict, filters)

    def pick_col(d: pd.DataFrame, prefer: List[str], fallback: List[str] | None = None):
        # Prefer real (non-null) columns first, then fall back to presence-only
        for n in prefer:
            if n in d.columns:
                try:
                    if d[n].notna().any():
                        return n
                except Exception:
                    return n
        for n in fallback or []:
            if n in d.columns:
                return n
        return None

    # 1) Average Total Score by Region (lollipop-like horizontal bar)
    fig_q1 = go.Figure()
    if not df_q1.empty:
        rcol = pick_col(df_q1, ["Region"], ["rgn"])
        scol = pick_col(df_q1, ["Average Total Score"], ["avg_total_score"])
        if rcol and scol:
            plot = df_q1.sort_values(scol, ascending=True)
            # Bar as base
            fig_q1 = px.bar(
                plot,
                y=rcol,
                x=scol,
                orientation="h",
                title=GRAPH_LABELS.get("q1", "Average Total Score by Region"),
                custom_data=[rcol],
                color_discrete_sequence=base_palette,
            )
            # Add markers to mimic lollipop heads
            try:
                fig_q1.add_trace(
                    go.Scatter(
                        y=plot[rcol],
                        x=plot[scol],
                        mode="markers",
                        marker=dict(color="#111827", size=6),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )
            except Exception:
                pass
            fig_q1.update_layout(uirevision="t1", margin=dict(t=24), height=420)
    if not fig_q1.data:
        fig_q1.update_layout(
            title=GRAPH_LABELS.get("q1", "Average Total Score by Region"),
            margin=dict(t=24),
        )

    # 2) 100% stacked bar: Category mix by Region (A/B/C/D) — compute % manually for compatibility
    fig_q2 = go.Figure()
    if not df_q1.empty:
        rcol = pick_col(df_q1, ["Region"], ["rgn"])
        cat_cols = [
            c for c in ["cat_a", "cat_b", "cat_c", "cat_d"] if c in df_q1.columns
        ]
        if rcol and cat_cols:
            mix = df_q1[[rcol] + cat_cols].copy()
            mix = mix.melt(id_vars=[rcol], var_name="category", value_name="count")
            # Friendly labels A/B/C/D
            try:
                mix["category"] = (
                    mix["category"].str.extract(r"cat_([abcd])")[0].str.upper()
                )
            except Exception:
                pass
            # Compute percentage per region
            try:
                totals = mix.groupby(rcol, dropna=False)["count"].transform("sum")
                mix["pct"] = (mix["count"] / totals) * 100.0
            except Exception:
                mix["pct"] = mix["count"]
            fig_q2 = px.bar(
                mix,
                x=rcol,
                y="pct",
                color="category",
                barmode="stack",
                title=GRAPH_LABELS.get("q2", "Category Mix by Region (100%)"),
                color_discrete_map=get_category_color_map(),
                custom_data=[rcol, "category"],
            )
            fig_q2.update_layout(uirevision="t1", margin=dict(t=24), height=420)
    if not fig_q2.data:
        fig_q2.update_layout(
            title=GRAPH_LABELS.get("q2", "Category Mix by Region (100%)"),
            margin=dict(t=24),
        )

    # 3) Scatter (single chart with drilldown on the same plot)
    # Default: region-level averages; When a single region is selected, show outlet-level points for that region
    fig_q3 = go.Figure()
    selected_regions = list((filters or {}).get("regions") or [])
    if (
        len(selected_regions) == 1
        and isinstance(df_q4, pd.DataFrame)
        and not df_q4.empty
    ):
        sel = selected_regions[0]
        # outlet-level scatter for the selected region
        s_outlet = pick_col(df_q4, ["Outlet", "sales_outlet", "outlet_name"])
        cat = pick_col(df_q4, ["Category", "outlet_category"])
        rq = pick_col(df_q4, ["Rate Quality", "rate_quality"])
        rp = pick_col(df_q4, ["Rate Performance", "rate_performance"])
        rg = pick_col(df_q4, ["Region", "rgn"])
        if rq and rp and cat:
            d = df_q4.copy()
            if rg:
                try:
                    d = d[d[rg] == sel]
                except Exception:
                    pass
            # Keep essential columns
            use_cols = [c for c in [rq, rp, cat, s_outlet, rg] if c]
            d = d[use_cols].dropna(subset=[rq, rp, cat])
            hover = [c for c in [s_outlet, rg, cat] if c]
            # Consistent category colors across app
            cat_map = get_category_color_map()
            fig_q3 = px.scatter(
                d,
                x=rq,
                y=rp,
                color=cat,
                hover_data=hover,
                title=f"Performance vs. Quality in {sel}",
                custom_data=[rg] if rg else None,
                color_discrete_map=cat_map,
            )
            fig_q3.update_traces(
                marker=dict(size=12, opacity=0.92, line=dict(width=1, color="#ffffff"))
            )
            fig_q3.update_layout(uirevision="t1", margin=dict(t=24), height=680)
    else:
        if not df_q1.empty:
            rcol = pick_col(df_q1, ["Region"], ["rgn"])
            xcol = pick_col(df_q1, ["Average Quality Rate"], ["avg_rate_quality"])
            ycol = pick_col(
                df_q1, ["Average Performance Rate"], ["avg_rate_performance"]
            )
            if rcol and xcol and ycol:
                # Brand palette for regions
                regs = df_q1[rcol].dropna().unique().tolist()
                reg_blue_map = color_map_from_list(regs, palette=brand_palette)
                fig_q3 = px.scatter(
                    df_q1,
                    x=xcol,
                    y=ycol,
                    text=rcol,
                    color=rcol,
                    title=GRAPH_LABELS.get("q3", "Performance vs. Quality by Region"),
                    color_discrete_map=reg_blue_map,
                    custom_data=[rcol],
                )
                # Reference means
                try:
                    fig_q3.add_hline(
                        y=float(df_q1[ycol].mean()),
                        line_dash="dot",
                        line_color="#9CA3AF",
                    )
                    fig_q3.add_vline(
                        x=float(df_q1[xcol].mean()),
                        line_dash="dot",
                        line_color="#9CA3AF",
                    )
                except Exception:
                    pass
                fig_q3.update_traces(
                    textposition="top center",
                    marker=dict(
                        size=13, opacity=0.95, line=dict(width=1, color="#ffffff")
                    ),
                )
                fig_q3.update_layout(uirevision="t1", margin=dict(t=24), height=680)
    if not fig_q3.data:
        fig_q3.update_layout(
            title=GRAPH_LABELS.get("q3", "Performance vs. Quality by Region"),
            margin=dict(t=24),
        )

    # 4) Top 20 Outlets by Score (from sheet1.q1 if outlet-level cols exist)
    fig_q4 = go.Figure()
    df_for_q4 = df_q4 if df_q4 is not None and not df_q4.empty else df_q1
    if not df_for_q4.empty:
        s = pick_col(df_for_q4, ["Outlet", "sales_outlet", "outlet_name"])
        ts = pick_col(df_for_q4, ["Total Score", "total_score"])
        oc = pick_col(df_for_q4, ["Category", "outlet_category"])
        rg = pick_col(df_for_q4, ["Region", "rgn"])
        if s and ts:
            plot = df_for_q4[
                [s, ts] + ([oc] if oc else []) + ([rg] if rg else [])
            ].dropna(subset=[s, ts])
            plot = (
                plot.sort_values(ts, ascending=False)
                .drop_duplicates(subset=[s])
                .head(20)
            )
            color = oc if oc else None
            custom = [rg, oc] if rg and oc else None
            fig_q4 = px.bar(
                plot,
                y=s,
                x=ts,
                orientation="h",
                color=color,
                title=GRAPH_LABELS.get("q4", "Top Outlets by Score"),
                custom_data=custom,
                color_discrete_sequence=base_palette,
            )
            fig_q4.update_layout(
                yaxis=dict(autorange="reversed"),
                uirevision="t1",
                margin=dict(t=24),
                height=420,
            )
    if not fig_q4.data:
        fig_q4.update_layout(
            title=GRAPH_LABELS.get("q4", "Top Outlets by Score"), margin=dict(t=24)
        )

    # 5) Bottom 20 Outlets by Score (from sheet1.q1 if available)
    fig_q5 = go.Figure()
    df_for_q5 = df_q5 if df_q5 is not None and not df_q5.empty else df_q1
    if not df_for_q5.empty:
        s = pick_col(df_for_q5, ["Outlet", "sales_outlet", "outlet_name"])
        ts = pick_col(df_for_q5, ["Total Score", "total_score"])
        oc = pick_col(df_for_q5, ["Category", "outlet_category"])
        rg = pick_col(df_for_q5, ["Region", "rgn"])
        if s and ts:
            plot = df_for_q5[
                [s, ts] + ([oc] if oc else []) + ([rg] if rg else [])
            ].dropna(subset=[s, ts])
            plot = (
                plot.sort_values(ts, ascending=True)
                .drop_duplicates(subset=[s])
                .head(20)
            )
            color = oc if oc else None
            custom = [rg, oc] if rg and oc else None
            fig_q5 = px.bar(
                plot,
                y=s,
                x=ts,
                orientation="h",
                color=color,
                title=GRAPH_LABELS.get("q5", "Bottom Outlets by Score"),
                custom_data=custom,
                color_discrete_sequence=base_palette,
            )
            fig_q5.update_layout(
                yaxis=dict(autorange="reversed"),
                uirevision="t1",
                margin=dict(t=24),
                height=420,
            )
    if not fig_q5.data:
        fig_q5.update_layout(
            title=GRAPH_LABELS.get("q5", "Bottom Outlets by Score"), margin=dict(t=24)
        )

    # 6) Outlet Count by Category (A/B/C/D) — Pie chart
    fig_q6 = go.Figure()
    if not df_q1.empty:
        # We can reuse detailed df_q4 (same as base) for counting
        detail = df_q4 if df_q4 is not None and not df_q4.empty else df_q1
        cat_col = pick_col(detail, ["Category", "outlet_category"])
        if cat_col:
            counts = (
                detail[[cat_col]]
                .dropna()
                .groupby(cat_col, dropna=False)
                .size()
                .reset_index(name="count")
            )
            # Order A-D if possible
            try:
                cat_order = ["A", "B", "C", "D"]
                counts[cat_col] = pd.Categorical(
                    counts[cat_col], categories=cat_order, ordered=True
                )
                counts = counts.sort_values(cat_col)
            except Exception:
                pass
            fig_q6 = px.pie(
                counts,
                names=cat_col,
                values="count",
                title="Number of Outlets by Category",
                color=cat_col,
                color_discrete_map=get_category_color_map(),
                hole=0.35,
            )
            fig_q6.update_traces(textposition="inside", textinfo="percent+label")
            fig_q6.update_layout(uirevision="t1", margin=dict(t=24), height=420)
    if not fig_q6.data:
        fig_q6.update_layout(title="Number of Outlets by Category", margin=dict(t=24))

    # If any figure empty, annotate reason for user clarity
    def annotate_if_empty(fig: go.Figure, title: str, need_cols: list[str]):
        if not fig.data:
            fig.add_annotation(
                text=f"No data available. Required columns: {', '.join(need_cols)}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(color="#6b7280"),
            )
            fig.update_layout(title=title, margin=dict(t=24))

    annotate_if_empty(
        fig_q1,
        GRAPH_LABELS.get("q1", "Average Total Score by Region"),
        ["rgn", "avg_total_score"],
    )
    annotate_if_empty(
        fig_q2,
        GRAPH_LABELS.get("q2", "Category Mix by Region (100%)"),
        ["rgn", "cat_a..cat_d"],
    )
    annotate_if_empty(
        fig_q3,
        GRAPH_LABELS.get("q3", "Performance vs. Quality by Region"),
        ["avg_rate_performance", "avg_rate_quality"],
    )
    annotate_if_empty(
        fig_q4,
        GRAPH_LABELS.get("q4", "Top Outlets by Score"),
        ["outlet_name", "total_score"],
    )
    annotate_if_empty(
        fig_q5,
        GRAPH_LABELS.get("q5", "Bottom Outlets by Score"),
        ["outlet_name", "total_score"],
    )

    return fig_q1, fig_q2, fig_q3, fig_q4, fig_q5, fig_q6
