from typing import Tuple, List, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def get_filtered_frames(data_dict: Dict[str, pd.DataFrame], filters: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Filter Tab 1 datasets (Sheet 1) based on global filters.

    Expected columns from sql_queries.sheet1:
      - q1: rgn, total_outlets, avg_total_score, avg_national_rank, avg_regional_rank
      - q2: outlet_category, avg_total_score, avg_new_car_reg, avg_intake_units, avg_revenue_performance
      - q3: rgn, outlet_category, outlet_count, avg_total_score, avg_national_rank, avg_regional_rank
      - q4: sales_outlet, rgn, outlet_category, total_score, rank_nationwide, rank_region, new_car_reg_unit, intake_unit, revenue_pct
      - q5: same as q4 (worst 20)
    """
    df_q1 = data_dict.get('q1', pd.DataFrame()).copy()
    df_q2 = data_dict.get('q2', pd.DataFrame()).copy()
    df_q3 = data_dict.get('q3', pd.DataFrame()).copy()
    df_q4 = data_dict.get('q4', pd.DataFrame()).copy()
    df_q5 = data_dict.get('q5', pd.DataFrame()).copy()

    # Apply filters: regions (rgn) and outlet_categories
    regions = filters.get('regions') or []
    cats = filters.get('outlet_categories') or []
    score_band = filters.get('score_band') or 'All'
    units_band = filters.get('units_band') or 'All'

    if regions and 'rgn' in df_q1.columns:
        df_q1 = df_q1[df_q1['rgn'].isin(regions)]
    if cats and 'outlet_category' in df_q2.columns:
        df_q2 = df_q2[df_q2['outlet_category'].isin(cats)]
    if regions and 'rgn' in df_q3.columns:
        df_q3 = df_q3[df_q3['rgn'].isin(regions)]
    if cats and 'outlet_category' in df_q3.columns:
        df_q3 = df_q3[df_q3['outlet_category'].isin(cats)]
    if regions and 'rgn' in df_q4.columns:
        df_q4 = df_q4[df_q4['rgn'].isin(regions)]
    if cats and 'outlet_category' in df_q4.columns:
        df_q4 = df_q4[df_q4['outlet_category'].isin(cats)]
    if regions and 'rgn' in df_q5.columns:
        df_q5 = df_q5[df_q5['rgn'].isin(regions)]
    if cats and 'outlet_category' in df_q5.columns:
        df_q5 = df_q5[df_q5['outlet_category'].isin(cats)]

    # Score band helper
    def apply_score_band(df, col):
        if col not in df.columns:
            return df
        if score_band == 'GE80':
            return df[df[col] >= 80]
        if score_band == '60_79':
            return df[(df[col] >= 60) & (df[col] <= 79)]
        if score_band == 'LT60':
            return df[df[col] < 60]
        return df

    # Units band helper (using simple absolute thresholds)
    def apply_units_band(df, col):
        if col not in df.columns:
            return df
        if units_band == 'GE50':
            return df[df[col] >= 50]
        if units_band == '20_49':
            return df[(df[col] >= 20) & (df[col] <= 49)]
        if units_band == 'LT20':
            return df[df[col] < 20]
        return df

    # Apply score band across frames
    df_q1 = apply_score_band(df_q1, 'avg_total_score')
    df_q2 = apply_score_band(df_q2, 'avg_total_score')
    df_q3 = apply_score_band(df_q3, 'avg_total_score')
    df_q4 = apply_score_band(df_q4, 'total_score')
    df_q5 = apply_score_band(df_q5, 'total_score')

    # Apply units band where relevant
    for col in ('avg_new_car_reg', 'avg_intake_units'):
        df_q2 = apply_units_band(df_q2, col)
    for col in ('new_car_reg_unit', 'intake_unit'):
        df_q4 = apply_units_band(df_q4, col)
        df_q5 = apply_units_band(df_q5, col)

    return df_q1, df_q2, df_q3, df_q4, df_q5


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
    """Return fig_q1..fig_q5 for Tab 1 given filters and palettes (new schema)."""
    df_q1, df_q2, df_q3, df_q4, df_q5 = get_filtered_frames(data_dict, filters)

    # 1) Regional Score Overview (horizontal bar)
    fig_q1 = go.Figure()
    if not df_q1.empty and 'rgn' in df_q1.columns and 'avg_total_score' in df_q1.columns:
        plot = df_q1.sort_values('avg_total_score', ascending=True)
        fig_q1 = px.bar(
            plot,
            y='rgn', x='avg_total_score', orientation='h',
            title=GRAPH_LABELS.get('q1', 'Regional Performance (Avg Score)'),
            custom_data=['rgn', 'total_outlets', 'avg_national_rank', 'avg_regional_rank'],
            pattern_shape_sequence=[""],
            color_discrete_sequence=base_palette
        )
        fig_q1.update_layout(uirevision='t1', margin=dict(t=24))
    else:
        fig_q1.update_layout(title=GRAPH_LABELS.get('q1', 'Regional Performance (Avg Score)'), margin=dict(t=24))

    # 2) Outlet Category Averages (grouped)
    fig_q2 = go.Figure()
    if not df_q2.empty and 'outlet_category' in df_q2.columns:
        # Use two primary metrics for readability; include others in hover
        melt_cols = []
        if 'avg_total_score' in df_q2.columns:
            melt_cols.append('avg_total_score')
        if 'avg_revenue_performance' in df_q2.columns:
            melt_cols.append('avg_revenue_performance')
        if not melt_cols:
            # fallback to any numeric columns except keys
            melt_cols = [c for c in df_q2.columns if c not in ['outlet_category']]
        long = df_q2.melt(id_vars=['outlet_category'], value_vars=melt_cols, var_name='metric', value_name='value')
        fig_q2 = px.bar(
            long, x='outlet_category', y='value', color='metric', barmode='group',
            title=GRAPH_LABELS.get('q2', 'Outlet Category Averages'),
            custom_data=['outlet_category'],
            pattern_shape_sequence=[""],
            color_discrete_sequence=base_palette
        )
        fig_q2.update_layout(uirevision='t1', margin=dict(t=24))
    else:
        fig_q2.update_layout(title=GRAPH_LABELS.get('q2', 'Outlet Category Averages'), margin=dict(t=24))

    # 3) Region × Category Heatmap (avg_total_score)
    fig_q3 = go.Figure()
    if not df_q3.empty and {'rgn', 'outlet_category'}.issubset(df_q3.columns):
        z = 'avg_total_score' if 'avg_total_score' in df_q3.columns else (
            'outlet_count' if 'outlet_count' in df_q3.columns else None
        )
        if z:
            piv = df_q3.pivot_table(index='rgn', columns='outlet_category', values=z, aggfunc='mean', fill_value=0)
            fig_q3 = px.imshow(
                piv.values, x=piv.columns.astype(str), y=piv.index.astype(str),
                aspect='auto', color_continuous_scale='Blues',
                title=GRAPH_LABELS.get('q3', 'Region × Category (Avg Score)')
            )
            # Preserve readable axes
            fig_q3.update_layout(uirevision='t1', margin=dict(t=24))
    else:
        fig_q3.update_layout(title=GRAPH_LABELS.get('q3', 'Region × Category (Avg Score)'), margin=dict(t=24))

    # 4) Top 20 Outlets by Score (barh)
    fig_q4 = go.Figure()
    if not df_q4.empty and {'sales_outlet', 'total_score'}.issubset(df_q4.columns):
        plot = df_q4.sort_values('total_score', ascending=False).head(20)
        color = 'outlet_category' if 'outlet_category' in plot.columns else None
        fig_q4 = px.bar(
            plot,
            y='sales_outlet', x='total_score', orientation='h', color=color,
            title=GRAPH_LABELS.get('q4', 'Top Outlets by Score'),
            custom_data=['rgn', 'outlet_category'] if {'rgn', 'outlet_category'}.issubset(plot.columns) else None,
            color_discrete_map=outlet_color_map if color == 'outlet_category' else None,
            category_orders={'outlet_category': all_outlet_categories} if color == 'outlet_category' else None,
            pattern_shape_sequence=[""],
            color_discrete_sequence=base_palette if color is None else None
        )
        fig_q4.update_layout(yaxis=dict(autorange='reversed'), uirevision='t1', margin=dict(t=24))
    else:
        fig_q4.update_layout(title=GRAPH_LABELS.get('q4', 'Top Outlets by Score'), margin=dict(t=24))

    # 5) Bottom 20 Outlets by Score (barh)
    fig_q5 = go.Figure()
    if not df_q5.empty and {'sales_outlet', 'total_score'}.issubset(df_q5.columns):
        plot = df_q5.sort_values('total_score', ascending=True).head(20)
        color = 'outlet_category' if 'outlet_category' in plot.columns else None
        fig_q5 = px.bar(
            plot,
            y='sales_outlet', x='total_score', orientation='h', color=color,
            title=GRAPH_LABELS.get('q5', 'Bottom Outlets by Score'),
            custom_data=['rgn', 'outlet_category'] if {'rgn', 'outlet_category'}.issubset(plot.columns) else None,
            color_discrete_map=outlet_color_map if color == 'outlet_category' else None,
            category_orders={'outlet_category': all_outlet_categories} if color == 'outlet_category' else None,
            pattern_shape_sequence=[""],
            color_discrete_sequence=base_palette if color is None else None
        )
        fig_q5.update_layout(yaxis=dict(autorange='reversed'), uirevision='t1', margin=dict(t=24))
    else:
        fig_q5.update_layout(title=GRAPH_LABELS.get('q5', 'Bottom Outlets by Score'), margin=dict(t=24))

    return fig_q1, fig_q2, fig_q3, fig_q4, fig_q5
