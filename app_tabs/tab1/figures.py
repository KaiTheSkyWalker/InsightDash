from typing import Tuple, List, Dict

import pandas as pd
import plotly.express as px


def get_filtered_frames(data_dict: Dict[str, pd.DataFrame], filters: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Filter tab1 datasets and return plotting variants where needed."""
    df_q1 = data_dict['q1'].copy()
    df_q2 = data_dict['q2'].copy()
    df_q3 = data_dict['q3'].copy()
    df_q4 = data_dict['q4'].copy()
    df_q5 = data_dict['q5'].copy()

    if filters.get('weeks'):
        w = filters['weeks']
        df_q1, df_q2, df_q3, df_q4, df_q5 = [df[df['week_number'].isin(w)] for df in [df_q1, df_q2, df_q3, df_q4, df_q5]]

    if filters.get('outlet_categories'):
        oc = filters['outlet_categories']
        df_q2, df_q3, df_q5 = [df[df['outlet_category'].isin(oc)] for df in [df_q2, df_q3, df_q5]]

    if filters.get('service_types'):
        st = filters['service_types']
        if 'service_type' in df_q3.columns:
            df_q3 = df_q3[df_q3['service_type'].isin(st)]

    if filters.get('regions'):
        rg = filters['regions']
        if 'region' in df_q4.columns:
            df_q4 = df_q4[df_q4['region'].isin(rg)]

    if filters.get('states'):
        stt = filters['states']
        if 'state' in df_q4.columns:
            df_q4 = df_q4[df_q4['state'].isin(stt)]

    if filters.get('customer_categories'):
        cc = filters['customer_categories']
        if 'customer_category' in df_q5.columns:
            df_q5 = df_q5[df_q5['customer_category'].isin(cc)]

    # plotted variants with 0 -> None for log axes
    df_q2_plot = df_q2.assign(market_share_plot=lambda d: d['market_share_percent'].replace(0, None))
    df_q3_plot = df_q3.assign(registrations_plot=lambda d: d['registrations'].replace(0, None))
    df_q4_plot = df_q4.assign(registrations_plot=lambda d: d['registrations'].replace(0, None))
    df_q5_plot = df_q5.assign(registrations_plot=lambda d: d['registrations'].replace(0, None))

    return df_q1, df_q2_plot, df_q3_plot, df_q4_plot, df_q5_plot


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
    """Return fig_q1..fig_q5 for Tab 1 given filters and palettes."""
    df_q1, df_q2_plot, df_q3_plot, df_q4_plot, df_q5_plot = get_filtered_frames(data_dict, filters)

    log_tickvals = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 50000, 100000]

    def create_fig(df, x, y, color=None, title="", custom_data=None, barmode='stack', log_y=True,
                   color_map=None, category_orders=None, yaxis_title=""):
        fig = px.bar(df, x=x, y=y, color=color, title=title, custom_data=custom_data, barmode=barmode,
                     log_y=log_y, color_discrete_map=color_map, category_orders=category_orders)
        fig.update_layout(yaxis_title=yaxis_title, uirevision='constant')
        if log_y:
            fig.update_yaxes(type='log', tickvals=log_tickvals, autorange=True)
        return fig

    fig_q1 = px.line(
        df_q1, x='week_number', y='total_registrations', title=GRAPH_LABELS['q1'], markers=True
    ).update_layout(uirevision='constant')
    fig_q1.update_traces(marker_color=base_palette[0], line_color=base_palette[0])

    fig_q2 = create_fig(
        df_q2_plot, 'week_number', 'market_share_plot', 'outlet_category',
        GRAPH_LABELS['q2'], ['outlet_category'], 'stack', False,
        outlet_color_map, {'outlet_category': all_outlet_categories}, 'Market Share (%)'
    )

    fig_q3 = create_fig(
        df_q3_plot, 'service_type', 'registrations_plot', 'outlet_category',
        GRAPH_LABELS['q3'], ['outlet_category'], 'group', True,
        outlet_color_map, {'outlet_category': all_outlet_categories}, 'Registrations (Log Scale)'
    )

    fig_q4 = create_fig(
        df_q4_plot, 'state', 'registrations_plot', 'region',
        GRAPH_LABELS['q4'], ['region'], 'stack', True,
        region_color_map, {'region': all_regions}, 'Registrations (Log Scale)'
    )

    fig_q5 = create_fig(
        df_q5_plot, 'customer_category', 'registrations_plot', 'outlet_category',
        GRAPH_LABELS['q5'], ['outlet_category'], 'group', True,
        outlet_color_map, {'outlet_category': all_outlet_categories}, 'Registrations (Log Scale)'
    )

    return fig_q1, fig_q2, fig_q3, fig_q4, fig_q5
