from typing import Dict, Tuple, Optional, List

import pandas as pd
from utils.colors import base_palette
import plotly.express as px
import plotly.graph_objects as go


def get_filtered_frames(tab2: Dict[str, pd.DataFrame], filters: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Filter Tab 2 datasets (Sheet 2) based on global filters.

    Expected columns from sql_queries.sheet2:
      - q1: rgn, avg_new_car_reg, avg_registration_rate, avg_gear_up_achievement, avg_customer_satisfaction_sales, avg_nps_sales
      - q2: outlet_category, avg_new_car_reg, avg_registration_rate, avg_gear_up_achievement, avg_insurance_renewal_first, avg_insurance_renewal_overall
      - q3: rgn, outlet_category, outlet_count, avg_new_car_reg, avg_gear_up_achievement, avg_insurance_renewal_first
      - q4: sales_outlet, rgn, outlet_category, new_car_reg_unit, new_car_reg_pct, gear_up_ach_pct, cs_sales_pct, nps_sales_pct, ins_renew_1st_pct, ins_renew_overall_pct, pov_pct
    """
    q1 = tab2.get('q1', pd.DataFrame()).copy()
    q2 = tab2.get('q2', pd.DataFrame()).copy()
    q3 = tab2.get('q3', pd.DataFrame()).copy()
    q4 = tab2.get('q4', pd.DataFrame()).copy()

    regions = filters.get('regions') or []
    cats = filters.get('outlet_categories') or []
    units_band = filters.get('units_band') or 'All'

    if regions and 'rgn' in q1.columns:
        q1 = q1[q1['rgn'].isin(regions)]
    if cats and 'outlet_category' in q2.columns:
        q2 = q2[q2['outlet_category'].isin(cats)]
    if regions and 'rgn' in q3.columns:
        q3 = q3[q3['rgn'].isin(regions)]
    if cats and 'outlet_category' in q3.columns:
        q3 = q3[q3['outlet_category'].isin(cats)]
    if regions and 'rgn' in q4.columns:
        q4 = q4[q4['rgn'].isin(regions)]
    if cats and 'outlet_category' in q4.columns:
        q4 = q4[q4['outlet_category'].isin(cats)]

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

    for col in ('avg_new_car_reg',):
        q1 = apply_units_band(q1, col)
        q2 = apply_units_band(q2, col)
        q3 = apply_units_band(q3, col)
    q4 = apply_units_band(q4, 'new_car_reg_unit')

    return q1, q2, q3, q4


def build_tab2_figures(
    tab2: Dict[str, pd.DataFrame],
    filters: Dict,
    outlet_color_map: Optional[Dict[str, str]] = None,
    region_color_map: Optional[Dict[str, str]] = None,
    all_outlet_categories: Optional[List[str]] = None,
    all_regions: Optional[List[str]] = None,
    labels: Optional[Dict[str, str]] = None,
    scatter_color_map: Optional[Dict[str, str]] = None,
):
    df1, df2, df3, df4 = get_filtered_frames(tab2, filters)

    # q1: Regional Efficiency Metrics (grouped bar)
    fig_q1 = go.Figure()
    if not df1.empty and 'rgn' in df1.columns:
        metrics = [
            c for c in ['avg_new_car_reg', 'avg_registration_rate', 'avg_gear_up_achievement', 'avg_customer_satisfaction_sales', 'avg_nps_sales']
            if c in df1.columns
        ]
        if metrics:
            long = df1.melt(id_vars=['rgn'], value_vars=metrics, var_name='metric', value_name='value')
            fig_q1 = px.bar(
                long, x='rgn', y='value', color='metric', barmode='group',
                title=(labels or {}).get('t2-graph-q1', 'Regional Efficiency Metrics'),
                custom_data=['rgn'],
                pattern_shape_sequence=[""],
                color_discrete_sequence=base_palette
            )
            fig_q1.update_layout(uirevision='t2', margin=dict(t=24))
    else:
        fig_q1.update_layout(title=(labels or {}).get('t2-graph-q1', 'Regional Efficiency Metrics'), margin=dict(t=24))

    # q2: Outlet Category Efficiency Metrics (grouped bar)
    fig_q2 = go.Figure()
    if not df2.empty and 'outlet_category' in df2.columns:
        metrics = [
            c for c in ['avg_new_car_reg', 'avg_registration_rate', 'avg_gear_up_achievement', 'avg_insurance_renewal_first', 'avg_insurance_renewal_overall']
            if c in df2.columns
        ]
        if metrics:
            long = df2.melt(id_vars=['outlet_category'], value_vars=metrics, var_name='metric', value_name='value')
            fig_q2 = px.bar(
                long, x='outlet_category', y='value', color='metric', barmode='group',
                title=(labels or {}).get('t2-graph-q2', 'Outlet Category Efficiency Metrics'),
                custom_data=['outlet_category'],
                pattern_shape_sequence=[""],
                color_discrete_sequence=base_palette
            )
            fig_q2.update_layout(uirevision='t2', margin=dict(t=24))
    else:
        fig_q2.update_layout(title=(labels or {}).get('t2-graph-q2', 'Outlet Category Efficiency Metrics'), margin=dict(t=24))

    # q3: Region × Category Heatmap (avg_new_car_reg)
    fig_q3 = go.Figure()
    if not df3.empty and {'rgn', 'outlet_category'}.issubset(df3.columns):
        z = 'avg_new_car_reg' if 'avg_new_car_reg' in df3.columns else (
            'avg_gear_up_achievement' if 'avg_gear_up_achievement' in df3.columns else None
        )
        if z:
            piv = df3.pivot_table(index='rgn', columns='outlet_category', values=z, aggfunc='mean', fill_value=0)
            fig_q3 = px.imshow(
                piv.values, x=piv.columns.astype(str), y=piv.index.astype(str),
                aspect='auto', color_continuous_scale='Blues',
                title=(labels or {}).get('t2-graph-q3', 'Region × Category (Avg New Car Reg)')
            )
            fig_q3.update_layout(uirevision='t2', margin=dict(t=24))
    else:
        fig_q3.update_layout(title=(labels or {}).get('t2-graph-q3', 'Region × Category (Avg New Car Reg)'), margin=dict(t=24))

    # q4a: Top outlets by new_car_reg_unit (barh)
    fig_q4a = go.Figure()
    if not df4.empty:
        df4a = df4.copy()
        if 'new_car_reg_unit' in df4a.columns:
            df4a = df4a.sort_values('new_car_reg_unit', ascending=False).head(15)
            label_col = 'sales_outlet' if 'sales_outlet' in df4a.columns else None
            if label_col:
                fig_q4a = px.bar(
                    df4a, y=label_col, x='new_car_reg_unit', orientation='h',
                    color='outlet_category' if 'outlet_category' in df4a.columns else None,
                    custom_data=['outlet_category'] if 'outlet_category' in df4a.columns else None,
                    title=(labels or {}).get('t2-graph-q4a', 'Top Outlets by New Car Reg (Top 15)'),
                    color_discrete_map=outlet_color_map or {},
                    category_orders={'outlet_category': all_outlet_categories or []},
                    pattern_shape_sequence=[""],
                    color_discrete_sequence=(base_palette if 'outlet_category' not in df4a.columns else None)
                )
                fig_q4a.update_layout(yaxis=dict(autorange='reversed'), uirevision='t2', margin=dict(t=24))
    if not fig_q4a.data:
        fig_q4a.update_layout(title=(labels or {}).get('t2-graph-q4a', 'Top Outlets by New Car Reg (Top 15)'), margin=dict(t=24))

    # q4b: Outlet scatter — Registration % vs NPS, size by units
    fig_q4b = go.Figure()
    if not df4.empty:
        df4b = df4.copy()
        xcol = 'new_car_reg_pct' if 'new_car_reg_pct' in df4b.columns else None
        ycol = 'nps_sales_pct' if 'nps_sales_pct' in df4b.columns else None
        size = 'new_car_reg_unit' if 'new_car_reg_unit' in df4b.columns else None
        color = 'outlet_category' if 'outlet_category' in df4b.columns else None
        if xcol and ycol:
            fig_q4b = px.scatter(
                df4b, x=xcol, y=ycol, size=size, color=color,
                title=(labels or {}).get('t2-graph-q4b', 'Outlet Registration% vs NPS'),
                custom_data=['rgn', 'outlet_category'] if {'rgn', 'outlet_category'}.issubset(df4b.columns) else None,
                color_discrete_map=(scatter_color_map or outlet_color_map or {}),
            )
            fig_q4b.update_layout(uirevision='t2', margin=dict(t=24))
    if not fig_q4b.data:
        fig_q4b.update_layout(title=(labels or {}).get('t2-graph-q4b', 'Outlet Registration% vs NPS'), margin=dict(t=24))

    return fig_q1, fig_q2, fig_q3, fig_q4a, fig_q4b
