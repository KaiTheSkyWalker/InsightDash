from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html


def _apply_filters(df: pd.DataFrame, f: Dict) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    if f.get('weeks') and 'week_number' in out.columns:
        out = out[out['week_number'].isin(f['weeks'])]
    if f.get('outlet_categories') and 'outlet_category' in out.columns:
        out = out[out['outlet_category'].isin(f['outlet_categories'])]
    if f.get('service_types') and 'service_type' in out.columns:
        out = out[out['service_type'].isin(f['service_types'])]
    if f.get('regions') and 'region' in out.columns:
        out = out[out['region'].isin(f['regions'])]
    if f.get('states') and 'state' in out.columns:
        out = out[out['state'].isin(f['states'])]
    if f.get('performance_tiers') and 'performance_tier' in out.columns:
        out = out[out['performance_tier'].isin(f['performance_tiers'])]
    if f.get('sales_center_codes') and 'sales_center_code' in out.columns:
        try:
            codes = set(str(x) for x in f['sales_center_codes'])
            out = out[out['sales_center_code'].astype(str).isin(codes)]
        except Exception:
            out = out[out['sales_center_code'].isin(f['sales_center_codes'])]
    return out


def _kpi_card(title: str, value: str, sub: str = "") -> html.Div:  # type: ignore[name-defined]
    return html.Div([
        html.Div(title, style={'fontSize': '12px', 'color': '#6b7280'}),
        html.Div(value, style={'fontSize': '20px', 'fontWeight': 800}),
        html.Div(sub, style={'fontSize': '11px', 'color': '#6b7280'}) if sub else None,
    ], style={
        'border': '1px solid #e5e7eb', 'borderRadius': '10px', 'padding': '10px 12px',
        'minWidth': '180px', 'backgroundColor': 'white', 'boxShadow': '0 1px 2px rgba(0,0,0,0.04)'
    })


def get_filtered_frames_simple(data: Dict[str, pd.DataFrame], filters: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return raw q1..q4 datasets for Tab 3 after applying filters."""
    q1 = _apply_filters(data.get('q1', pd.DataFrame()), filters)
    q2 = _apply_filters(data.get('q2', pd.DataFrame()), filters)
    q3 = _apply_filters(data.get('q3', pd.DataFrame()), filters)
    q4 = _apply_filters(data.get('q4', pd.DataFrame()), filters)
    return q1, q2, q3, q4


def merged_for_chart2(q2: pd.DataFrame, q3: pd.DataFrame) -> pd.DataFrame:
    """Build the merged dataset used conceptually by Chart 2 (quadrant)."""
    cats_df = pd.DataFrame({'outlet_category': []})
    if not q2.empty and 'outlet_category' in q2.columns:
        cats_df = pd.DataFrame({'outlet_category': pd.Index(q2['outlet_category'].dropna().unique())})
    if not q3.empty and 'outlet_category' in q3.columns:
        q3cats = pd.Index(q3['outlet_category'].dropna().unique())
        base = pd.Index(cats_df['outlet_category']) if not cats_df.empty else pd.Index([])
        cats_df = pd.DataFrame({'outlet_category': list(base.union(q3cats))})

    agg_q2 = pd.DataFrame()
    if not q2.empty and 'outlet_category' in q2.columns:
        agg_map = {}
        if 'registrations' in q2.columns:
            agg_map['registrations'] = 'sum'
        elif 'total_registrations' in q2.columns:
            agg_map['total_registrations'] = 'sum'
        if 'avg_vehicle_value' in q2.columns:
            agg_map['avg_vehicle_value'] = 'mean'
        if 'total_sales_value' in q2.columns:
            agg_map['total_sales_value'] = 'sum'
        if 'value_per_processing_day' in q2.columns:
            agg_map['value_per_processing_day'] = 'mean'
        if agg_map:
            agg_q2 = q2.groupby('outlet_category', dropna=False).agg(agg_map).reset_index()
            if 'total_registrations' in agg_q2.columns and 'registrations' not in agg_q2.columns:
                agg_q2 = agg_q2.rename(columns={'total_registrations': 'registrations'})

    agg_q3 = pd.DataFrame()
    if not q3.empty and 'outlet_category' in q3.columns:
        if 'avg_processing_days' in q3.columns:
            agg_q3 = q3.groupby('outlet_category', dropna=False)['avg_processing_days'].mean().reset_index()

    m = cats_df.copy()
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
) -> Tuple[go.Figure, go.Figure, go.Figure, go.Figure, go.Figure]:
    """Build Alternative 1 for Tab 3.

    Returns:
      - fig1 (Chart 1), fig2 (Chart 2), fig3 (Chart 3), fig5 (Chart 5)
      - kpi_children (list of Divs), table_columns (list), table_data (list)
    """
    q1 = _apply_filters(data.get('q1', pd.DataFrame()), filters)
    q2 = _apply_filters(data.get('q2', pd.DataFrame()), filters)
    q3 = _apply_filters(data.get('q3', pd.DataFrame()), filters)
    q4 = _apply_filters(data.get('q4', pd.DataFrame()), filters)

    # 1) Week-over-Week Category Race (Grouped Bars)
    fig1 = go.Figure()
    if not q2.empty and {'week_number', 'outlet_category'}.issubset(q2.columns):
        ycol = 'registrations' if 'registrations' in q2.columns else 'total_registrations' if 'total_registrations' in q2.columns else None
        if ycol:
            df_plot = q2[['week_number', 'outlet_category', ycol]].copy()
            fig1 = px.bar(
                df_plot, x='week_number', y=ycol, color='outlet_category', barmode='group',
                custom_data=['week_number', 'outlet_category'],
                title=(labels or {}).get('t3-graph-1', 'Weekly Performance Overview'),
                color_discrete_map=outlet_color_map or {},
                category_orders={'outlet_category': all_outlet_categories or []}
            )
            fig1.update_layout(uirevision='t3', hovermode='x unified')
    else:
        fig1.update_layout(title='Week-over-Week Category Race (insufficient data)')

    # 2) Efficiency & Value Quadrant (Scatter)
    fig2 = go.Figure()
    # Aggregate by outlet_category from q2 (value metrics) and q3 (efficiency)
    # Build a base category list to prevent KeyError on merge
    cats_df = pd.DataFrame({'outlet_category': []})
    if not q2.empty and 'outlet_category' in q2.columns:
        cats_df = pd.DataFrame({'outlet_category': pd.Index(q2['outlet_category'].dropna().unique())})
    if not q3.empty and 'outlet_category' in q3.columns:
        q3cats = pd.Index(q3['outlet_category'].dropna().unique())
        base = pd.Index(cats_df['outlet_category']) if not cats_df.empty else pd.Index([])
        cats_df = pd.DataFrame({'outlet_category': list(base.union(q3cats))})

    agg_q2 = pd.DataFrame()
    if not q2.empty and 'outlet_category' in q2.columns:
        agg_map = {}
        if 'registrations' in q2.columns:
            agg_map['registrations'] = 'sum'
        elif 'total_registrations' in q2.columns:
            agg_map['total_registrations'] = 'sum'
        if 'avg_vehicle_value' in q2.columns:
            agg_map['avg_vehicle_value'] = 'mean'
        if 'total_sales_value' in q2.columns:
            agg_map['total_sales_value'] = 'sum'
        if 'value_per_processing_day' in q2.columns:
            agg_map['value_per_processing_day'] = 'mean'
        if agg_map:
            agg_q2 = q2.groupby('outlet_category', dropna=False).agg(agg_map).reset_index()
            if 'total_registrations' in agg_q2.columns and 'registrations' not in agg_q2.columns:
                agg_q2 = agg_q2.rename(columns={'total_registrations': 'registrations'})
    agg_q3 = pd.DataFrame()
    if not q3.empty and 'outlet_category' in q3.columns:
        if 'avg_processing_days' in q3.columns:
            agg_q3 = q3.groupby('outlet_category', dropna=False)['avg_processing_days'].mean().reset_index()
        else:
            agg_q3 = pd.DataFrame(columns=['outlet_category', 'avg_processing_days'])

    # Start with cats_df, then left-merge whatever aggregates exist
    m = cats_df.copy()
    if not agg_q2.empty:
        m = m.merge(agg_q2, on='outlet_category', how='left')
    if not agg_q3.empty:
        m = m.merge(agg_q3, on='outlet_category', how='left')

    # Ensure required columns exist, even if NaN
    for c in ['registrations', 'avg_vehicle_value', 'avg_processing_days', 'total_sales_value', 'value_per_processing_day']:
        if c not in m.columns:
            m[c] = None

    if not m.empty and 'outlet_category' in m.columns and 'registrations' in m.columns:
        fig2 = px.scatter(
            m, x='avg_processing_days', y='avg_vehicle_value', size='registrations', color='outlet_category',
            hover_data=['outlet_category', 'total_sales_value', 'value_per_processing_day'],
            custom_data=['outlet_category'],
            title=(labels or {}).get('t3-graph-2', 'Efficiency & Value Quadrant'),
            color_discrete_map=outlet_color_map or {},
            category_orders={'outlet_category': all_outlet_categories or []}
        )
        # Quadrant lines at means
        try:
            xmean = float(m['avg_processing_days'].dropna().mean())
            ymean = float(m['avg_vehicle_value'].dropna().mean())
            fig2.add_vline(x=xmean, line_dash='dash', line_color='#9ca3af')
            fig2.add_hline(y=ymean, line_dash='dash', line_color='#9ca3af')
        except Exception:
            pass
        fig2.update_layout(uirevision='t3')
    else:
        fig2.update_layout(title='Efficiency & Value Quadrant (insufficient data)')

    # 3) Performance Tier Contribution (100% Stacked)
    fig3 = go.Figure()
    if not q3.empty and {'performance_tier'}.issubset(q3.columns):
        # Aggregate totals by tier, robust to missing columns
        agg_cols = {}
        if 'total_sales_value' in q3.columns:
            agg_cols['total_sales_value'] = 'sum'
        reg_col_name = None
        if 'total_registrations' in q3.columns:
            agg_cols['total_registrations'] = 'sum'
            reg_col_name = 'total_registrations'
        elif 'registrations' in q3.columns:
            agg_cols['registrations'] = 'sum'
            reg_col_name = 'registrations'
        if not agg_cols:
            # Fallback: use counts only
            tiers = q3.groupby('performance_tier', dropna=False).size().reset_index(name='registrations')
        else:
            tiers = q3.groupby('performance_tier', dropna=False).agg(agg_cols).reset_index()
        # Build long dataframe for stacked normalization
        value_vars = []
        if 'total_sales_value' in tiers.columns:
            value_vars.append('total_sales_value')
        if reg_col_name and reg_col_name in tiers.columns:
            value_vars.append(reg_col_name)
        if not value_vars:
            tiers['registrations'] = tiers.get('registrations', 0)
            value_vars = ['registrations']
        long_df = pd.melt(tiers, id_vars=['performance_tier'], value_vars=value_vars, var_name='metric', value_name='value')
        tier_order = ['HIGH_PERFORMER','GOOD_PERFORMER','AVERAGE_PERFORMER','NEEDS_IMPROVEMENT']
        fig3 = px.bar(
            long_df, x='metric', y='value', color='performance_tier',
            custom_data=['performance_tier'],
            title=(labels or {}).get('t3-graph-3', 'Sales Centers Performance Tier Contribution'),
            color_discrete_map=tier_colors or {},
            category_orders={'performance_tier': tier_order}
        )
        # barnorm='percent' puts the axis in units 0..100. Using '.0%' would multiply by 100 again.
        # Keep axis as 0..100 with a percent suffix for correct labeling.
        fig3.update_layout(barmode='stack', barnorm='percent', uirevision='t3')
        fig3.update_yaxes(range=[0, 100], tickformat='.0f', ticksuffix='%')
    else:
        fig3.update_layout(title='Performance Tier Contribution (insufficient data)')

    # 4) Top Performers (Horizontal Bar)
    fig4 = go.Figure()
    if not q3.empty and {'sales_center_code', 'composite_score'}.issubset(q3.columns):
        top = q3.copy()
        # Choose label
        ylab = 'sales_center_name' if 'sales_center_name' in top.columns else 'sales_center_code'
        # Create metric safely
        metric = 'composite_score' if 'composite_score' in top.columns else None
        if metric:
            top = top.sort_values(metric, ascending=False, na_position='last').head(10)
            tier_order = ['HIGH_PERFORMER','GOOD_PERFORMER','AVERAGE_PERFORMER','NEEDS_IMPROVEMENT']
            fig4 = px.bar(
                top,
                y=ylab,
                x=metric,
                orientation='h',
                color='performance_tier' if 'performance_tier' in top.columns else None,
                custom_data=['sales_center_code'],
                title=(labels or {}).get('t3-graph-4', 'Top Performers of Sales Centers'),
                color_discrete_map=(tier_colors or {}) if 'performance_tier' in top.columns else None,
                category_orders={'performance_tier': tier_order}
            )
            fig4.update_layout(yaxis=dict(autorange='reversed'), uirevision='t3')
    else:
        fig4.update_layout(title='Top Performers (insufficient data)')

    # 5) Salesman/Center Performance (Bar Chart)
    fig5 = go.Figure()
    if not q4.empty and 'sales_center_code' in q4.columns:
        df = q4.copy()
        # Ensure code string, pick metrics
        try:
            df['sales_center_code'] = df['sales_center_code'].astype(str)
        except Exception:
            pass
        reg_col = 'registrations' if 'registrations' in df.columns else 'total_registrations' if 'total_registrations' in df.columns else None
        if reg_col is None:
            df['registrations'] = 1
            reg_col = 'registrations'
        # Aggregate by center
        agg = {reg_col: 'sum'}
        if 'avg_deal_value' in df.columns:
            agg['avg_deal_value'] = 'mean'
        label_col = 'sales_center_name' if 'sales_center_name' in df.columns else 'sales_center_code'
        group_keys = ['sales_center_code']
        if label_col != 'sales_center_code':
            group_keys.append(label_col)
        g = df.groupby(group_keys, dropna=False).agg(agg).reset_index()
        # Normalize column names
        if reg_col != 'registrations':
            g = g.rename(columns={reg_col: 'registrations'})
        # Sort and take top N for readability
        g = g.sort_values('registrations', ascending=False).head(25)
        # Build horizontal bar, color by avg_deal_value if present
        color_arg = 'avg_deal_value' if 'avg_deal_value' in g.columns else None
        fig5 = px.bar(
            g,
            y=label_col,
            x='registrations',
            orientation='h',
            color=color_arg,
            color_continuous_scale='Viridis' if color_arg else None,
            custom_data=['sales_center_code'],
            title=(labels or {}).get('t3-graph-5', 'Sales Center Performance (Top)')
        )
        fig5.update_layout(uirevision='t3', yaxis=dict(autorange='reversed'))
    else:
        fig5.update_layout(title='Center Performance (insufficient data)')

    return fig1, fig2, fig3, fig4, fig5
