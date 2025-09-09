from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.colors import base_palette


def _apply_filters(df: pd.DataFrame, f: Dict) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    # Primary global filters
    if f.get('outlet_categories') and 'outlet_category' in out.columns:
        out = out[out['outlet_category'].isin(f['outlet_categories'])]
    if f.get('regions') and 'rgn' in out.columns:
        out = out[out['rgn'].isin(f['regions'])]
    # Numeric filters
    units_band = f.get('units_band') or 'All'

    # Local-only filter (reuse name sales_center_codes for service_outlet)
    if f.get('sales_center_codes'):
        codes = set(str(x) for x in f['sales_center_codes'])
        if 'service_outlet' in out.columns:
            out = out[out['service_outlet'].astype(str).isin(codes)]
        elif 'sales_center_code' in out.columns:
            out = out[out['sales_center_code'].astype(str).isin(codes)]
    # Apply units range where available
    if units_band != 'All':
        if 'avg_intake_units' in out.columns:
            if units_band == 'GE50':
                out = out[out['avg_intake_units'] >= 50]
            elif units_band == '20_49':
                out = out[(out['avg_intake_units'] >= 20) & (out['avg_intake_units'] <= 49)]
            elif units_band == 'LT20':
                out = out[out['avg_intake_units'] < 20]
        if 'intake_unit' in out.columns:
            if units_band == 'GE50':
                out = out[out['intake_unit'] >= 50]
            elif units_band == '20_49':
                out = out[(out['intake_unit'] >= 20) & (out['intake_unit'] <= 49)]
            elif units_band == 'LT20':
                out = out[out['intake_unit'] < 20]
    return out


## Removed unused _kpi_card helper (not referenced)


def get_filtered_frames_simple(data: Dict[str, pd.DataFrame], filters: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return raw q1..q4 datasets for Tab 3 after applying filters."""
    q1 = _apply_filters(data.get('q1', pd.DataFrame()), filters)
    q2 = _apply_filters(data.get('q2', pd.DataFrame()), filters)
    q3 = _apply_filters(data.get('q3', pd.DataFrame()), filters)
    q4 = _apply_filters(data.get('q4', pd.DataFrame()), filters)
    return q1, q2, q3, q4


def merged_for_chart2(q2: pd.DataFrame, q3: pd.DataFrame) -> pd.DataFrame:
    """Merge category-level value and quality metrics for Tab 3 Chart 2 table view."""
    cats = pd.DataFrame({'outlet_category': []})
    if not q2.empty and 'outlet_category' in q2.columns:
        cats = pd.DataFrame({'outlet_category': pd.Index(q2['outlet_category'].dropna().unique())})
    if not q3.empty and 'outlet_category' in q3.columns:
        oc3 = pd.Index(q3['outlet_category'].dropna().unique())
        base = pd.Index(cats['outlet_category']) if not cats.empty else pd.Index([])
        cats = pd.DataFrame({'outlet_category': list(base.union(oc3))})

    agg_q2 = pd.DataFrame()
    if not q2.empty and 'outlet_category' in q2.columns:
        cols = [c for c in q2.columns if c != 'outlet_category']
        agg_q2 = q2.groupby('outlet_category', dropna=False)[cols].mean(numeric_only=True).reset_index()

    agg_q3 = pd.DataFrame()
    if not q3.empty and 'outlet_category' in q3.columns:
        cols = [c for c in q3.columns if c != 'outlet_category' and c != 'rgn']
        agg_q3 = q3.groupby('outlet_category', dropna=False)[cols].mean(numeric_only=True).reset_index()

    m = cats.copy()
    if not agg_q2.empty:
        m = m.merge(agg_q2, on='outlet_category', how='left')
    if not agg_q3.empty:
        m = m.merge(agg_q3, on='outlet_category', how='left')
    return m


def build_tab3_figures(
    data: Dict[str, pd.DataFrame],
    filters: Dict,
    outlet_color_map: Dict[str, str] | None = None,
    tier_colors: Dict[str, str] | None = None,
    all_outlet_categories: List[str] | None = None,
    labels: Dict[str, str] | None = None,
    scatter_color_map: Dict[str, str] | None = None,
) -> Tuple[go.Figure, go.Figure, go.Figure, go.Figure, go.Figure]:
    """Build five charts for Tab 3 aligned to Sheet 3 (Value & Performance)."""
    q1 = _apply_filters(data.get('q1', pd.DataFrame()), filters)
    q2 = _apply_filters(data.get('q2', pd.DataFrame()), filters)
    q3 = _apply_filters(data.get('q3', pd.DataFrame()), filters)
    q4 = _apply_filters(data.get('q4', pd.DataFrame()), filters)

    # 1) Regional Value & Ops Metrics (grouped bar)
    fig1 = go.Figure()
    if not q1.empty and 'rgn' in q1.columns:
        metrics = [c for c in ['avg_intake_units', 'avg_intake_percentage', 'avg_revenue_performance', 'avg_parts_performance', 'avg_lubricant_performance'] if c in q1.columns]
        if metrics:
            long = q1.melt(id_vars=['rgn'], value_vars=metrics, var_name='metric', value_name='value')
            fig1 = px.bar(
                long, x='rgn', y='value', color='metric', barmode='group',
                title=(labels or {}).get('t3-graph-1', 'Regional Value & Ops Metrics'),
                custom_data=['rgn'],
                pattern_shape_sequence=[""],
                color_discrete_sequence=base_palette
            )
            fig1.update_layout(uirevision='t3', margin=dict(t=24))
    else:
        fig1.update_layout(title=(labels or {}).get('t3-graph-1', 'Regional Value & Ops Metrics'), margin=dict(t=24))

    # 2) Category Value & Ops Metrics (grouped bar)
    fig2 = go.Figure()
    if not q2.empty and 'outlet_category' in q2.columns:
        metrics = [c for c in ['avg_intake_units', 'avg_intake_percentage', 'avg_revenue_performance', 'avg_eappointment_adoption', 'avg_quality_performance_index'] if c in q2.columns]
        if metrics:
            long = q2.melt(id_vars=['outlet_category'], value_vars=metrics, var_name='metric', value_name='value')
            fig2 = px.bar(
                long, x='outlet_category', y='value', color='metric', barmode='group',
                title=(labels or {}).get('t3-graph-2', 'Category Value & Ops Metrics'),
                custom_data=['outlet_category'],
                pattern_shape_sequence=[""],
                color_discrete_sequence=base_palette
            )
            fig2.update_layout(uirevision='t3', margin=dict(t=24))
    else:
        fig2.update_layout(title=(labels or {}).get('t3-graph-2', 'Category Value & Ops Metrics'), margin=dict(t=24))

    # 3) Region × Category Heatmap (Quality Performance Index)
    fig3 = go.Figure()
    if not q3.empty and {'rgn', 'outlet_category'}.issubset(q3.columns):
        z = 'avg_quality_performance_index' if 'avg_quality_performance_index' in q3.columns else (
            'avg_customer_satisfaction_service' if 'avg_customer_satisfaction_service' in q3.columns else None
        )
        if z:
            piv = q3.pivot_table(index='rgn', columns='outlet_category', values=z, aggfunc='mean', fill_value=0)
            fig3 = px.imshow(
                piv.values, x=piv.columns.astype(str), y=piv.index.astype(str),
                aspect='auto', color_continuous_scale='Blues',
                title=(labels or {}).get('t3-graph-3', 'Region × Category (Quality Index)')
            )
            fig3.update_layout(uirevision='t3', margin=dict(t=24))
    else:
        fig3.update_layout(title=(labels or {}).get('t3-graph-3', 'Region × Category (Quality Index)'), margin=dict(t=24))

    # 4) Top Service Outlets by Intake Units (barh)
    fig4 = go.Figure()
    if not q4.empty and {'service_outlet', 'intake_unit'}.issubset(q4.columns):
        top = q4.sort_values('intake_unit', ascending=False, na_position='last').head(15)
        fig4 = px.bar(
            top, y='service_outlet', x='intake_unit', orientation='h',
            color='outlet_category' if 'outlet_category' in top.columns else None,
            custom_data=['service_outlet'],
            title=(labels or {}).get('t3-graph-4', 'Top Service Outlets by Intake Units'),
            pattern_shape_sequence=[""],
            color_discrete_sequence=(base_palette if 'outlet_category' not in top.columns else None),
            color_discrete_map=(outlet_color_map or {}) if 'outlet_category' in top.columns else None,
            category_orders={'outlet_category': (all_outlet_categories or [])} if 'outlet_category' in top.columns else None
        )
        fig4.update_layout(yaxis=dict(autorange='reversed'), uirevision='t3', margin=dict(t=24))
    else:
        fig4.update_layout(title=(labels or {}).get('t3-graph-4', 'Top Service Outlets by Intake Units'), margin=dict(t=24))

    # 5) Service Outlet: CS% vs QPI% (scatter)
    fig5 = go.Figure()
    if not q4.empty and {'cs_service_pct', 'qpi_pct'}.issubset(q4.columns):
        fig5 = px.scatter(
            q4, x='cs_service_pct', y='qpi_pct', size='intake_unit' if 'intake_unit' in q4.columns else None,
            color='outlet_category' if 'outlet_category' in q4.columns else None,
            custom_data=['service_outlet'] if 'service_outlet' in q4.columns else None,
            title=(labels or {}).get('t3-graph-5', 'Service CS% vs QPI%'),
            color_discrete_map=((scatter_color_map or outlet_color_map or {})) if 'outlet_category' in q4.columns else None,
            category_orders={'outlet_category': (all_outlet_categories or [])} if 'outlet_category' in q4.columns else None
        )
        fig5.update_layout(uirevision='t3', margin=dict(t=24))
    else:
        fig5.update_layout(title=(labels or {}).get('t3-graph-5', 'Service CS% vs QPI%'), margin=dict(t=24))

    return fig1, fig2, fig3, fig4, fig5
