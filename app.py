import dash
from dash import dcc, html, Input, Output, State, ctx
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import sys
import os
import json
from itertools import cycle, islice
from dash_resizable_panels import PanelGroup, Panel, PanelResizeHandle

# ---------- LLM (Gemini) optional setup ----------
HAVE_NEW_GENAI = False
HAVE_LEGACY_GENAI = False
try:
    from google import genai
    HAVE_NEW_GENAI = True
except Exception:
    try:
        import google.generativeai as genai_legacy
        HAVE_LEGACY_GENAI = True
    except Exception:
        pass

try:
    from config.api import GOOGLE_API_KEY
except Exception:
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

MODEL_NAME = "gemini-1.5-flash"  # use "gemini-1.5-pro" for deeper analysis

# ---------- Data source ----------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from data_layer.tab_1 import get_tab1_results

# ---------- Fonts / styles ----------
external_stylesheets = ['https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap']


def create_dashboard(data_dict):
    """
    Dash app with cross-filtering, stable colors, multi-chart select,
    and Gemini-based summarizer in a resizable, toggleable sidebar.
    """
    app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=external_stylesheets)

    # ----- Helpers -----
    def uniq(series_list):
        vals = pd.Index([])
        for s in series_list:
            if s is not None:
                vals = vals.union(pd.Index(s.dropna().unique()))
        return list(vals)

    # --- COLOR THEME UPDATE ---
    # New color theme based on the user-provided image.
    base_palette = [
        '#E73489',  # Bright Pink
        '#7E32A8',  # Purple
        '#49319B',  # Dark Blue
        '#3B63C4',  # Medium Blue
        '#45B4D3',  # Light Blue
    ]

    def color_map_from_list(keys, palette=base_palette):
        # Extend palette if there are more keys than colors to avoid harsh cycling
        extended_palette = list(islice(cycle(palette), len(keys)))
        return dict(zip(keys, extended_palette))


    def pack_df(df: pd.DataFrame, max_rows: int = 300):
        recs = df.head(max_rows).to_dict('records')
        return {"columns": list(df.columns), "records": recs, "n_rows": int(len(df))}

    # ----- Data & filters -----
    all_weeks = sorted(data_dict['q1']['week_number'].dropna().unique())

    all_outlet_categories = sorted(uniq([
        data_dict.get('q2', pd.DataFrame()).get('outlet_category'),
        data_dict.get('q3', pd.DataFrame()).get('outlet_category'),
        data_dict.get('q5', pd.DataFrame()).get('outlet_category'),
    ]))

    all_regions = sorted(data_dict['q4']['region'].dropna().unique()) if 'region' in data_dict['q4'].columns else []
    all_customer_categories = sorted(data_dict['q5']['customer_category'].dropna().unique()) if 'customer_category' in data_dict['q5'].columns else []
    all_service_types = sorted(data_dict['q3']['service_type'].dropna().unique()) if 'service_type' in data_dict['q3'].columns else []
    all_states = sorted(data_dict['q4']['state'].dropna().unique()) if 'state' in data_dict['q4'].columns else []

    outlet_color_map = color_map_from_list(all_outlet_categories)
    region_color_map = color_map_from_list(all_regions)

    default_filters = {
        'weeks': [], 'outlet_categories': [], 'regions': [],
        'customer_categories': [], 'service_types': [], 'states': [],
    }

    GRAPH_LABELS = {
        'q1': 'Weekly Registration Overview',
        'q2': 'Outlet Category Market Share (Log Scale)',
        'q3': 'Service Type Breakdown (Log Scale)',
        'q4': 'Regional Registration Distribution (Log Scale)',
        'q5': 'Customer Category Registrations (Log Scale)'
    }

    def get_filtered_frames(filters):
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
            df_q3 = df_q3[df_q3['service_type'].isin(st)]

        if filters.get('regions'):
            rg = filters['regions']
            df_q4 = df_q4[df_q4['region'].isin(rg)]

        if filters.get('states'):
            stt = filters['states']
            df_q4 = df_q4[df_q4['state'].isin(stt)]

        if filters.get('customer_categories'):
            cc = filters['customer_categories']
            df_q5 = df_q5[df_q5['customer_category'].isin(cc)]

        # plotted variants with 0 -> None for log axes
        df_q2_plot = df_q2.assign(market_share_plot=lambda d: d['market_share_percent'].replace(0, None))
        df_q3_plot = df_q3.assign(registrations_plot=lambda d: d['registrations'].replace(0, None))
        df_q4_plot = df_q4.assign(registrations_plot=lambda d: d['registrations'].replace(0, None))
        df_q5_plot = df_q5.assign(registrations_plot=lambda d: d['registrations'].replace(0, None))

        return df_q1, df_q2_plot, df_q3_plot, df_q4_plot, df_q5_plot

    # ----- Layout -----
    app.layout = html.Div([
        PanelGroup(
            id="main-panel-group",
            direction="horizontal",
            autoSaveId="vrdb-split",  # persist widths
            children=[
                # Main Content Panel
                Panel(
                    id="main-panel",
                    children=[
                        html.Div(id='main-content', children=[
                            html.Div([
                                html.H1("Vehicle Registration Dashboard", style={'textAlign': 'center', 'flex': '1'}),
                                html.Button('☰', id='sidebar-toggle-button', n_clicks=0,
                                            style={'height': '36px', 'marginLeft': '20px'}),
                            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
                                      'paddingRight': '20px'}),

                            dcc.Store(id='filter-store', data=default_filters),
                            dcc.Store(id='active-selection', data=None),

                            # Start CLOSED; also track if we've ever opened before
                            dcc.Store(id='sidebar-visibility-store', data={'visible': False, 'opened_once': False}),

                            dcc.Store(id='selected-graphs', data=[]),
                            dcc.Store(id='selected-data', data={}),

                            html.Div([
                                html.Div(dcc.Dropdown(
                                    id='week-filter', placeholder="Select Week(s)",
                                    options=[{'label': f'Week {w}', 'value': w} for w in all_weeks], multi=True
                                ), style={'flex': '1', 'margin': '0 10px'}),
                                html.Div(dcc.Dropdown(
                                    id='outlet-category-filter', placeholder="Select Outlet Category(s)",
                                    options=[{'label': cat, 'value': cat} for cat in all_outlet_categories], multi=True
                                ), style={'flex': '1', 'margin': '0 10px'}),
                                html.Div(dcc.Dropdown(
                                    id='region-filter', placeholder="Select Region(s)",
                                    options=[{'label': reg, 'value': reg} for reg in all_regions], multi=True
                                ), style={'flex': '1', 'margin': '0 10px'}),
                                html.Div(dcc.Dropdown(
                                    id='customer-category-filter', placeholder="Select Customer Category(s)",
                                    options=[{'label': cat, 'value': cat} for cat in all_customer_categories],
                                    multi=True
                                ), style={'flex': '1', 'margin': '0 10px'}),
                                html.Button('Reset All Filters', id='reset-button', n_clicks=0,
                                            style={'height': '36px', 'marginLeft': '10px'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'padding': '10px 20px',
                                      'backgroundColor': '#f0f0f0'}),

                            html.Div([
                                html.Div([
                                    dcc.Graph(id='graph-q1'),
                                    html.Button("Select this graph", id='btn-select-q1', n_clicks=0,
                                                style={'marginTop': '6px'})
                                ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                                html.Div([
                                    dcc.Graph(id='graph-q2'),
                                    html.Button("Select this graph", id='btn-select-q2', n_clicks=0,
                                                style={'marginTop': '6px'})
                                ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                                html.Div([
                                    dcc.Graph(id='graph-q3'),
                                    html.Button("Select this graph", id='btn-select-q3', n_clicks=0,
                                                style={'marginTop': '6px'})
                                ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                                html.Div([
                                    dcc.Graph(id='graph-q4'),
                                    html.Button("Select this graph", id='btn-select-q4', n_clicks=0,
                                                style={'marginTop': '6px'})
                                ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                                html.Div([
                                    dcc.Graph(id='graph-q5'),
                                    html.Button("Select this graph", id='btn-select-q5', n_clicks=0,
                                                style={'marginTop': '6px'})
                                ], style={'width': '98%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                            ])
                        ], style={
                            'padding': '20px',
                            'fontFamily': '"Roboto", sans-serif'
                        }),
                    ],
                    style={'height': '100vh', 'overflowY': 'auto'}
                ),

                # Resize Handle (start hidden)
                PanelResizeHandle(
                    id='sidebar-resize-handle',
                    children=html.Div(style={
                        "backgroundColor": "#ccc",
                        "width": "5px",
                        "cursor": "col-resize"
                    }),
                    style={'display': 'none'}
                ),

                # Sidebar Panel (start CLOSED)
                Panel(
                    id="sidebar-panel",
                    children=[
                        html.Div(
                            id='sidebar',
                            children=[
                                html.H2("Controls",
                                        style={'margin': '8px 0 4px 0', 'lineHeight': '1.1', 'fontWeight': 800}),
                                html.P("Select charts to generate insights",
                                       style={'margin': '0', 'color': '#6b7280', 'fontSize': '13px'}),

                                # Selected chips / placeholder
                                html.Div(
                                    id='selected-info',
                                    children=[html.Div("No charts selected yet.", style={'color': '#6b7280', 'fontSize': '13px'})],
                                    style={'margin': '4px 0 0 0'}
                                ),

                                html.Button(
                                    'Generate Insights',
                                    id='generate-button',
                                    n_clicks=0,
                                    style={
                                        'width': '100%', 'padding': '12px', 'marginTop': '10px',
                                        'backgroundColor': '#007bff', 'color': 'white', 'border': 'none',
                                        'borderRadius': '8px', 'cursor': 'pointer'
                                    }
                                ),
                                html.Div(id='generate-output')
                            ],
                            style={
                                'padding': '16px 20px 20px',
                                'backgroundColor': '#f8f9fa',
                                'display': 'flex', 'flexDirection': 'column',
                                'gap': '6px',
                                'height': '100%', 'minHeight': 0,
                                'overflowY': 'auto', 'overflowX': 'hidden',
                                'WebkitOverflowScrolling': 'touch', 'overscrollBehavior': 'contain'
                            }
                        )
                    ],
                    style={'minWidth': 0, 'width': 0, 'display': 'none', 'height': '100vh', 'backgroundColor': '#f8f9fa'}
                )
            ],
        )
    ], style={'height': '100vh', 'fontFamily': '"Roboto", sans-serif'})

    # ----- Toggle sidebar visibility -----
    @app.callback(
        Output('sidebar-panel', 'style'),
        Output('sidebar-resize-handle', 'style'),
        Output('sidebar-visibility-store', 'data'),
        Input('sidebar-toggle-button', 'n_clicks'),
        State('sidebar-visibility-store', 'data'),
        prevent_initial_call=True
    )
    def toggle_sidebar_visibility(n_clicks, visibility_data):
        if not n_clicks:
            raise PreventUpdate

        is_visible = bool(visibility_data.get('visible', False))
        opened_once = bool(visibility_data.get('opened_once', False))
        new_visibility = not is_visible

        if new_visibility:
            # OPENING
            if not opened_once:
                # First-ever open: force width to 200px
                panel_style = {
                    'height': '100vh',
                    'backgroundColor': '#f8f9fa',
                    'width': '200px'
                }
                new_store = {'visible': True, 'opened_once': True}
            else:
                # Subsequent opens: let saved/resized width be used
                panel_style = {
                    'height': '100vh',
                    'backgroundColor': '#f8f9fa'
                }
                new_store = {'visible': True, 'opened_once': True}

            handle_style = {"width": "5px", "cursor": "col-resize", "backgroundColor": "#ccc"}
            return panel_style, handle_style, new_store

        else:
            # CLOSING
            panel_style = {'minWidth': 0, 'width': 0, 'display': 'none', 'height': '100vh', 'backgroundColor': '#f8f9fa'}
            handle_style = {'display': 'none'}
            new_store = {'visible': False, 'opened_once': opened_once}
            return panel_style, handle_style, new_store

    # ----- Generate report (multi-chart) -----
    @app.callback(
        Output('generate-output', 'children'),
        Input('generate-button', 'n_clicks'),
        State('selected-graphs', 'data'),
        State('selected-data', 'data'),
        State('filter-store', 'data'),
        prevent_initial_call=True
    )
    def generate_report(n_clicks, selected_graphs, selected_data, filters):
        if not n_clicks:
            return ""
        if not selected_graphs:
            return html.Div([
                html.H4("No charts selected.", style={'color': '#991B1B'}),
                html.P("Use “Select this graph” under one or more charts.")
            ])

        def label(gid):
            return GRAPH_LABELS.get(gid, gid)

        charts_payload = []
        for gid in selected_graphs:
            meta = (selected_data or {}).get(gid)
            if not meta:
                continue
            charts_payload.append({
                "graph_id": gid,
                "graph_label": label(gid),
                "filters": filters,
                "columns": meta.get("columns", []),
                "n_rows": meta.get("n_rows", 0),
                "rows": meta.get("records", [])
            })

        if not charts_payload:
            return html.Div([
                html.H4("No data available.", style={'color': '#991B1B'}),
                html.P("Re-select charts after adjusting filters.")
            ])

        payload = {"charts": charts_payload}
        prompt = (
            "You are a data analyst. I will provide multiple chart datasets as JSON.\n"
            "Need to be detailed"
            "For each chart, return concise markdown:\n"
            "### <Chart Title>\n"
            "- **Overview** (1–2 sentences)\n"
            "- **Highlights** (3–5 bullets: trends, outliers, comparisons)\n"
            "- **Notables** (edge cases or data quality flags)\n"
            "- **Next Step** (one actionable suggestion)\n"
            "JSON follows:\n```json\n"
            + json.dumps(payload, ensure_ascii=False)
            + "\n```"
        )

        llm_text = None
        try:
            if HAVE_NEW_GENAI and GOOGLE_API_KEY:
                client = genai.Client(api_key=GOOGLE_API_KEY)
                resp = client.models.generate_content(model=MODEL_NAME, contents=[prompt])
                llm_text = getattr(resp, "text", None)
            elif HAVE_LEGACY_GENAI and GOOGLE_API_KEY:
                genai_legacy.configure(api_key=GOOGLE_API_KEY)
                model = genai_legacy.GenerativeModel(MODEL_NAME)
                resp = model.generate_content([prompt])
                llm_text = getattr(resp, "text", None)
            else:
                llm_text = (
                    "LLM not configured. Install `google-genai` or `google-generativeai` and set `GOOGLE_API_KEY`."
                )
        except Exception as e:
            return html.Div([
                html.H4("Error Generating Report", style={'color': '#991B1B'}),
                html.P(f"LLM error: {e}")
            ])

        return html.Div([
            html.H4("Report", style={'color': '#007bff'}),
            dcc.Markdown(llm_text or "_No content returned._", link_target="_blank")
        ])

    # ----- Filter controller: click-to-filter, toggle off by clicking again -----
    @app.callback(
        Output('filter-store', 'data'),
        Output('active-selection', 'data'),
        Output('week-filter', 'value'),
        Output('outlet-category-filter', 'value'),
        Output('region-filter', 'value'),
        Output('customer-category-filter', 'value'),
        Input('reset-button', 'n_clicks'),
        Input('week-filter', 'value'),
        Input('outlet-category-filter', 'value'),
        Input('region-filter', 'value'),
        Input('customer-category-filter', 'value'),
        Input('graph-q1', 'clickData'),
        Input('graph-q2', 'clickData'),
        Input('graph-q3', 'clickData'),
        Input('graph-q4', 'clickData'),
        Input('graph-q5', 'clickData'),
        State('filter-store', 'data'),
        State('active-selection', 'data'),
        prevent_initial_call=True
    )
    def update_filters_and_ui(
        reset_clicks, weeks, outlet_cats, regions, customer_cats,
        click_q1, click_q2, click_q3, click_q4, click_q5,
        current_filters, active_selection
    ):
        def make_key(graph_id, point):
            def _cd(p, i=0, default=None):
                try:
                    return p.get('customdata', [default])[i]
                except Exception:
                    return default

            if graph_id == 'graph-q1': return f"q1|week={point['x']}"
            if graph_id == 'graph-q2': return f"q2|week={point['x']}|outlet={_cd(point)}"
            if graph_id == 'graph-q3': return f"q3|service={point['x']}|outlet={_cd(point)}"
            if graph_id == 'graph-q4': return f"q4|state={point['x']}|region={_cd(point)}"
            if graph_id == 'graph-q5': return f"q5|customer={point['x']}|outlet={_cd(point)}"
            return None

        trig = ctx.triggered[0]
        trig_id = trig['prop_id'].split('.')[0]

        if trig_id == 'reset-button':
            return default_filters, None, [], [], [], []

        if trig_id in ('week-filter', 'outlet-category-filter', 'region-filter', 'customer-category-filter'):
            new_filters = current_filters.copy()
            new_filters['weeks'] = weeks or []
            new_filters['outlet_categories'] = outlet_cats or []
            new_filters['regions'] = regions or []
            new_filters['customer_categories'] = customer_cats or []
            return (new_filters, None, new_filters['weeks'], new_filters['outlet_categories'],
                    new_filters['regions'], new_filters['customer_categories'])

        if trig_id.startswith('graph-') and trig.get('value'):
            point = trig['value']['points'][0]
            key = make_key(trig_id, point)

            if active_selection == key:
                return default_filters, None, [], [], [], []

            new_filters = default_filters.copy()
            if trig_id == 'graph-q1':
                new_filters['weeks'] = [point['x']]
            elif trig_id == 'graph-q2':
                new_filters['weeks'] = [point['x']]
                new_filters['outlet_categories'] = [point['customdata'][0]]
            elif trig_id == 'graph-q3':
                new_filters['service_types'] = [point['x']]
                new_filters['outlet_categories'] = [point['customdata'][0]]
            elif trig_id == 'graph-q4':
                new_filters['states'] = [point['x']]
                new_filters['regions'] = [point['customdata'][0]]
            elif trig_id == 'graph-q5':
                new_filters['customer_categories'] = [point['x']]
                new_filters['outlet_categories'] = [point['customdata'][0]]

            return (new_filters, key, new_filters.get('weeks', []), new_filters.get('outlet_categories', []),
                    new_filters.get('regions', []), new_filters.get('customer_categories', []))

        return (current_filters, active_selection, current_filters.get('weeks', []),
                current_filters.get('outlet_categories', []), current_filters.get('regions', []),
                current_filters.get('customer_categories', []))

    # ----- Plot updates (stable colors via color_discrete_map) -----
    @app.callback(
        Output('graph-q1', 'figure'), Output('graph-q2', 'figure'),
        Output('graph-q3', 'figure'), Output('graph-q4', 'figure'),
        Output('graph-q5', 'figure'), Input('filter-store', 'data')
    )
    def update_graphs(filters):
        df_q1, df_q2_plot, df_q3_plot, df_q4_plot, df_q5_plot = get_filtered_frames(filters)

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
        # Apply new theme color to the line chart
        fig_q1.update_traces(marker_color=base_palette[0], line_color=base_palette[0])


        fig_q2 = create_fig(
            df_q2_plot, 'week_number', 'market_share_plot', 'outlet_category',
            GRAPH_LABELS['q2'], ['outlet_category'], 'stack', True,
            outlet_color_map, {'outlet_category': all_outlet_categories}, 'Market Share (%) (Log Scale)'
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

    # ----- Multi-select buttons: capture selections & store snapshots -----
    @app.callback(
        Output('selected-graphs', 'data'),
        Output('selected-data', 'data'),
        Output('selected-info', 'children'),
        Input('btn-select-q1', 'n_clicks'),
        Input('btn-select-q2', 'n_clicks'),
        Input('btn-select-q3', 'n_clicks'),
        Input('btn-select-q4', 'n_clicks'),
        Input('btn-select-q5', 'n_clicks'),
        State('filter-store', 'data'),
        State('selected-graphs', 'data'),
        State('selected-data', 'data'),
        prevent_initial_call=True
    )
    def handle_select(btn1, btn2, btn3, btn4, btn5, filters, selected_graphs, selected_data):
        triggered = ctx.triggered_id
        if triggered is None:
            raise PreventUpdate

        df_q1, df_q2_plot, df_q3_plot, df_q4_plot, df_q5_plot = get_filtered_frames(filters)

        id_map = {
            'btn-select-q1': ('q1', df_q1),
            'btn-select-q2': ('q2', df_q2_plot),
            'btn-select-q3': ('q3', df_q3_plot),
            'btn-select-q4': ('q4', df_q4_plot),
            'btn-select-q5': ('q5', df_q5_plot),
        }
        graph_id, df = id_map[triggered]

        selected_graphs = list(selected_graphs or [])
        selected_data = dict(selected_data or {})

        if graph_id in selected_graphs:
            # toggle off
            selected_graphs = [g for g in selected_graphs if g != graph_id]
            selected_data.pop(graph_id, None)
        else:
            # toggle on (snapshot)
            selected_graphs.append(graph_id)
            selected_data[graph_id] = pack_df(df)

        def label(gid):
            return GRAPH_LABELS.get(gid, gid)

        if not selected_graphs:
            info = html.Div("No charts selected yet.", style={'color': '#6b7280', 'fontSize': '13px'})
            return selected_graphs, selected_data, info

        # chip style
        def chip(text):
            return html.Span(
                text,
                style={
                    'display': 'inline-block',
                    'padding': '4px 10px',
                    'margin': '6px 6px 0 0',
                    'backgroundColor': '#e8f0fe',
                    'border': '1px solid #d0e2ff',
                    'borderRadius': '9999px',
                    'fontSize': '12px',
                    'color': '#1e3a8a',
                    'fontWeight': 600,
                    'whiteSpace': 'nowrap'
                }
            )

        chips = [chip(label(gid)) for gid in selected_graphs]
        info = html.Div([
            html.Div(f"Selected ({len(selected_graphs)})", style={'fontWeight': 700, 'fontSize': '13px'}),
            html.Div(chips, style={'display': 'flex', 'flexWrap': 'wrap'})
        ])

        return selected_graphs, selected_data, info

    return app


# ---------- Main ----------
if __name__ == '__main__':
    try:
        data_dict = get_tab1_results()
        app = create_dashboard(data_dict)
        app.run(debug=True, port=8090)
    except ImportError:
        print("Error: Could not import 'get_tab1_results' from 'data_layer.tab_1'.")
        print("Please ensure the file exists and the 'src' directory is in your Python path.")
    except Exception as e:
        print(f"An error occurred during app setup: {e}")