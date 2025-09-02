from typing import Dict, Tuple, Optional, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.colors import base_palette


# Palette for Tab 2 visuals (reference) — high‑contrast blues
t2_palette = [
    '#0B2E4E', '#1E3A8A', '#1D4ED8', '#2563EB', '#3B82F6',
    '#60A5FA', '#0EA5E9', '#38BDF8', '#0891B2', '#06B6D4'
]


def get_filtered_frames(tab2: Dict[str, pd.DataFrame], filters: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    q1 = tab2.get('q1', pd.DataFrame()).copy()
    q2 = tab2.get('q2', pd.DataFrame()).copy()
    q3 = tab2.get('q3', pd.DataFrame()).copy()
    q4 = tab2.get('q4', pd.DataFrame()).copy()

    if filters.get('weeks'):
        if 'week_number' in q1.columns:
            q1 = q1[q1['week_number'].isin(filters['weeks'])]
        if 'week_number' in q2.columns:
            q2 = q2[q2['week_number'].isin(filters['weeks'])]
        if 'week_number' in q3.columns:
            q3 = q3[q3['week_number'].isin(filters['weeks'])]
        if 'week_number' in q4.columns:
            q4 = q4[q4['week_number'].isin(filters['weeks'])]
    if filters.get('outlet_categories'):
        if 'outlet_category' in q2.columns:
            q2 = q2[q2['outlet_category'].isin(filters['outlet_categories'])]
        if 'outlet_category' in q3.columns:
            q3 = q3[q3['outlet_category'].isin(filters['outlet_categories'])]
    if filters.get('service_types'):
        if 'service_type' in q3.columns:
            q3 = q3[q3['service_type'].isin(filters['service_types'])]
    if filters.get('regions'):
        if 'region' in q4.columns:
            q4 = q4[q4['region'].isin(filters['regions'])]
    if filters.get('states'):
        if 'state' in q4.columns:
            q4 = q4[q4['state'].isin(filters['states'])]

    return q1, q2, q3, q4


def build_tab2_figures(
    tab2: Dict[str, pd.DataFrame],
    filters: Dict,
    outlet_color_map: Optional[Dict[str, str]] = None,
    region_color_map: Optional[Dict[str, str]] = None,
    all_outlet_categories: Optional[List[str]] = None,
    all_regions: Optional[List[str]] = None,
    labels: Optional[Dict[str, str]] = None,
):
    df1, df2, df3, df4 = get_filtered_frames(tab2, filters)

    # q1: Weekly Trends (bar + 2 lines, dual y)
    fig_q1 = make_subplots(specs=[[{"secondary_y": True}]])
    if not df1.empty:
        x = df1.get('week_number')
        total = df1.get('total_registrations')
        avg_days = df1.get('avg_processing_days')
        fast_rate = df1.get('fast_processing_rate_percent')

        if total is not None:
            fig_q1.add_trace(go.Bar(name='Total Registrations', x=x, y=total, marker_color=base_palette[0]), secondary_y=False)
        if avg_days is not None:
            fig_q1.add_trace(go.Scatter(name='Avg Processing Days', x=x, y=avg_days,
                                        mode='lines+markers', marker=dict(size=6),
                                        line=dict(width=2, color=base_palette[2])), secondary_y=True)
        if fast_rate is not None:
            fig_q1.add_trace(go.Scatter(name='Fast Processing %', x=x, y=fast_rate,
                                        mode='lines+markers', marker=dict(size=6),
                                        line=dict(width=2, dash='dash', color=base_palette[3])), secondary_y=True)
    fig_q1.update_layout(title=(labels or {}).get('t2-graph-q1', 'Weekly Trends'), barmode='group', uirevision='t2_constant', hovermode='x unified')
    fig_q1.update_yaxes(title_text="Registrations", secondary_y=False)
    fig_q1.update_yaxes(title_text="Days / %", secondary_y=True)

    # q2: Outlet Category Performance by Week (grouped)
    if not df2.empty:
        df2_plot = df2.copy()
        if 'registrations' not in df2_plot.columns and 'total_registrations' in df2_plot.columns:
            df2_plot['registrations'] = df2_plot['total_registrations']
        fig_q2 = px.bar(
            df2_plot, x='week_number', y='registrations', color='outlet_category',
            barmode='group', title=(labels or {}).get('t2-graph-q2', 'Outlet Category Performance by Week'),
            custom_data=['outlet_category'],
            color_discrete_map=outlet_color_map or {},
            category_orders={'outlet_category': all_outlet_categories or []}
        )
        fig_q2.update_layout(uirevision='t2_constant')
    else:
        fig_q2 = go.Figure().update_layout(title='Outlet Category Performance by Week')

    # q3: Outlet Category × Service Type (heatmap)
    if not df3.empty and {'outlet_category', 'service_type'}.issubset(df3.columns):
        zcol = 'registrations'
        if zcol not in df3.columns:
            zcol = next((c for c in ['avg_processing_days', 'fast_processing_rate_percent', 'avg_data_completeness_percent'] if c in df3.columns), None)
        if zcol:
            pivot = df3.pivot_table(index='outlet_category', columns='service_type', values=zcol, aggfunc='sum', fill_value=0)
            fig_q3 = go.Figure(data=go.Heatmap(z=pivot.values, x=pivot.columns.astype(str), y=pivot.index.astype(str), coloraxis="coloraxis"))
            fig_q3.update_layout(title=(labels or {}).get('t2-graph-q3', f'Category × Service Type Heatmap'), coloraxis=dict(colorbar=dict(title=zcol)), uirevision='t2_constant')
        else:
            fig_q3 = go.Figure().update_layout(title=(labels or {}).get('t2-graph-q3', 'Category × Service Type Heatmap'))
    else:
        fig_q3 = go.Figure().update_layout(title=(labels or {}).get('t2-graph-q3', 'Category × Service Type Heatmap'))

    # q4a: Efficiency ranking (Top N)
    fig_q4a = go.Figure()
    if not df4.empty:
        df4a = df4.copy()
        label_col = None
        for cand in ['sales_center_name', 'sales_center_code', 'state']:
            if cand in df4a.columns:
                label_col = cand
                break
        score_col = None
        if 'fast_processing_rate_percent' in df4a.columns:
            score_col = 'fast_processing_rate_percent'
            df4a = df4a.sort_values(score_col, ascending=False).head(15)
        elif 'avg_processing_days' in df4a.columns:
            score_col = 'avg_processing_days'
            df4a = df4a.sort_values(score_col, ascending=True).head(15)
        elif 'registrations' in df4a.columns:
            score_col = 'registrations'
            df4a = df4a.sort_values(score_col, ascending=False).head(15)

        if label_col and score_col:
            fig_q4a = px.bar(
                df4a, y=label_col, x=score_col, orientation='h',
                color=df4a.get('outlet_category') if 'outlet_category' in df4a.columns else None,
                custom_data=['outlet_category'] if 'outlet_category' in df4a.columns else None,
                title=(labels or {}).get('t2-graph-q4a', 'Efficiency Ranking (Top 15)'),
                color_discrete_map=outlet_color_map or {},
                category_orders={'outlet_category': all_outlet_categories or []}
            )
            fig_q4a.update_layout(yaxis=dict(autorange='reversed'), uirevision='t2_constant')
        else:
            fig_q4a.update_layout(title=(labels or {}).get('t2-graph-q4a', 'Efficiency Ranking (Top 15)'))
    else:
        fig_q4a.update_layout(title='Efficiency Ranking (Top N)')

    # q4b: Regional/State distribution (bar)
    fig_q4b = go.Figure().update_layout(title='Regional / State Distribution')
    if not df4.empty:
        region_col = 'region' if 'region' in df4.columns else None
        state_col = 'state' if 'state' in df4.columns else None

        candidate_metrics = ['registrations', 'outlets_active', 'total_registrations', 'active_outlets', 'count', 'n']
        metric = next((c for c in candidate_metrics if c in df4.columns), None)

        def group_sum(df, by_cols, metric_name):
            if metric_name:
                g = (df.groupby(by_cols, dropna=False)[metric_name].sum().reset_index())
            else:
                g = (df.groupby(by_cols, dropna=False).size().reset_index(name='rows'))
            return g

        if region_col and state_col:
            grp = group_sum(df4, [region_col, state_col], metric)
            ycol = metric if metric else 'rows'
            fig_q4b = px.bar(
                grp, x=state_col, y=ycol, color=region_col, title='Regional / State Distribution',
                custom_data=[region_col] if region_col in grp.columns else None,
                color_discrete_map=region_color_map or {},
                category_orders={'region': all_regions or []}
            )
            fig_q4b.update_layout(xaxis={'categoryorder': 'total descending'}, uirevision='t2_constant')
        elif state_col:
            grp = group_sum(df4, [state_col], metric)
            ycol = metric if metric else 'rows'
            fig_q4b = px.bar(grp, x=state_col, y=ycol, title=(labels or {}).get('t2-graph-q4b', 'Regional / State Distribution'))
            fig_q4b.update_layout(xaxis={'categoryorder': 'total descending'}, uirevision='t2_constant')
        elif region_col:
            grp = group_sum(df4, [region_col], metric)
            ycol = metric if metric else 'rows'
            fig_q4b = px.bar(
                grp, x=region_col, y=ycol, title='Regional Distribution',
                color=region_col if region_col in grp.columns else None,
                color_discrete_map=region_color_map or {},
                category_orders={'region': all_regions or []}
            )
            fig_q4b.update_layout(xaxis={'categoryorder': 'total descending'}, uirevision='t2_constant')
        else:
            label_col = next((c for c in ['sales_center_name', 'sales_center_code'] if c in df4.columns), None)
            if label_col:
                if not metric:
                    grp = (df4.groupby([label_col], dropna=False).size().reset_index(name='rows').sort_values('rows', ascending=False).head(15))
                    fig_q4b = px.bar(grp, x=label_col, y='rows', title='Distribution by Center')
                else:
                    grp = (df4.groupby([label_col], dropna=False)[metric].sum().reset_index().sort_values(metric, ascending=False).head(15))
                    fig_q4b = px.bar(grp, x=label_col, y=metric, title='Distribution by Center')
                fig_q4b.update_layout(uirevision='t2_constant')

    return fig_q1, fig_q2, fig_q3, fig_q4a, fig_q4b
