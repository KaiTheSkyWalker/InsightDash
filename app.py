import dash
import re
from dash import dcc, html, Input, Output, State, ctx, no_update
from dash import dash_table
from dash.exceptions import PreventUpdate
import pandas as pd
import json
from dash_resizable_panels import PanelGroup, Panel, PanelResizeHandle
 

from data_layer.tab_1 import get_tab1_results
from data_layer.tab_2 import get_tab2_results
from data_layer.tab_3 import get_tab3_results
from config.settings import GOOGLE_API_KEY, MODEL_NAME
from services.llm import generate_markdown_from_prompt
from utils.data import uniq, pack_df
from utils.colors import color_map_from_list, base_palette, tier_color_map
from app_tabs.tab1.layout import get_layout as tab1_layout
from app_tabs.tab2.layout import get_layout as tab2_layout
from app_tabs.tab3.layout import get_layout as tab3_layout
from app_tabs.tab1.figures import get_filtered_frames as t1_get_filtered_frames, build_tab1_figures
from app_tabs.tab2.figures import build_tab2_figures
from app_tabs.tab3.figures import build_tab3_figures, get_filtered_frames_simple as t3_get_filtered_frames, merged_for_chart2
from app_tabs.tab2.figures import get_filtered_frames as t2_get_filtered_frames
from loguru import logger
from config.logging import configure_logging

# Configure logging early so all modules use the same sink
configure_logging()
tab3_logger = logger.bind(tab="Tab3")

"""
Configuration and LLM are now centralized in config.settings and services.llm.
MODEL_NAME and GOOGLE_API_KEY are imported from settings.
"""


# ---------- Fonts / styles ----------
external_stylesheets = ['https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap']


def create_dashboard(data_dict, data_dict_2, data_dict_3=None):
    """
    Dash app with cross-filtering, stable colors, multi-chart select,
    and Gemini-based summarizer in a resizable, toggleable sidebar.
    """
    # local alias for Tab 2 dataset (prevents NameError in inner functions)
    tab2 = data_dict_2 or {}

    app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=external_stylesheets)

    # Helpers moved to utils.data and utils.colors

    # ----- Data & filters -----
    all_weeks = sorted(data_dict['q1']['week_number'].dropna().unique())

    all_outlet_categories = sorted(uniq([
        data_dict.get('q2', pd.DataFrame()).get('outlet_category'),
        data_dict.get('q3', pd.DataFrame()).get('outlet_category'),
        data_dict.get('q5', pd.DataFrame()).get('outlet_category'),
    ]))

    all_regions = sorted(data_dict['q4']['region'].dropna().unique()) if 'region' in data_dict['q4'].columns else []
    all_customer_categories = sorted(data_dict['q5']['customer_category'].dropna().unique()) if 'customer_category' in data_dict['q5'].columns else []

    outlet_color_map = color_map_from_list(all_outlet_categories)
    region_color_map = color_map_from_list(all_regions)

    default_filters = {
        'weeks': [], 'outlet_categories': [], 'regions': [],
        'customer_categories': [], 'service_types': [], 'states': [],
    }

    GRAPH_LABELS = {
        'q1': 'Weekly Registration Overview',
        'q2': 'Outlet Category Market Share',
        'q3': 'Service Type Breakdown (Log Scale)',
        'q4': 'Regional Registration Distribution (Log Scale)',
        'q5': 'Customer Category Registrations (Log Scale)',
        # Tab 2
        't2-graph-q1': 'Weekly Trends',
        't2-graph-q2': 'Outlet Category Performance by Week',
        't2-graph-q3': 'Category × Service Type Heatmap',
        't2-graph-q4a': 'Efficiency Ranking (Top 15)',
        't2-graph-q4b': 'Regional / State Distribution',
        # Tab 3
        't3-graph-1': 'Weekly Performance Overview',
        't3-graph-2': 'Efficiency & Value Quadrant',
        't3-graph-3': 'Sales Centers Performance Tier Contribution',
        't3-graph-4': 'Top Performers of Sales Centers',
        't3-graph-5': 'Sales Center Performance (Top)',
    }


    # ----- Layout -----
    app.layout = html.Div([
        PanelGroup(
            id="main-panel-group",
            direction="horizontal",
            autoSaveId="vrdb-split",  # persist widths
            style={'height': '100dvh', 'minHeight': 0},

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
                            # Tab 3 dedicated filter store
                            dcc.Store(id='tab3-filter-store', data={
                                'weeks': [], 'outlet_categories': [], 'performance_tiers': [], 'sales_center_codes': []
                            }),

                            # ---- Filter bar ----
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

                            # --------- Tabs ---------
                            dcc.Tabs(
                                id="tabs",
                                value="tab1",
                                children=[
                                    # ===== TAB 1: Dashboard =====
                                    dcc.Tab(label="Overview", value="tab1", children=[tab1_layout()]),

                                    # ===== TAB 2: Deep-dive (graphs) =====
                                    dcc.Tab(label="Operational Insights", value="tab2", children=[tab2_layout()]),

                                    # ===== TAB 3: 5-Chart Dashboard =====
                                    dcc.Tab(label="Performance Analyzer", value="tab3", children=[tab3_layout()]),
                                ],
                                style={'marginTop': '10px'}
                            ),
                        ], style={
                            'padding': '20px',
                            'fontFamily': '"Roboto", sans-serif'
                        }),
                    ],
                    style={'height': '100vh', 'overflowY': 'auto'}
                ),

                PanelResizeHandle(
                    id='sidebar-resize-handle',
                    children=html.Div(style={
                        "backgroundColor": "#ccc",
                        "width": "5px",
                        "cursor": "col-resize"
                    }),
                    style={'display': 'none'}
                ),

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
                                    'Clear Selection',
                                    id='clear-selection',
                                    n_clicks=0,
                                    style={
                                        'width': '100%', 'padding': '10px', 'marginTop': '6px',
                                        'backgroundColor': '#e5e7eb', 'color': '#111827', 'border': '1px solid #d1d5db',
                                        'borderRadius': '8px', 'cursor': 'pointer'
                                    }
                                ),

                                # LLM data scope removed; always use full data for analysis

                                # Insight mode selector
                                html.Div([
                                    html.Label("Analysis Mode", style={'fontWeight': 'bold', 'fontSize': '14px', 'marginTop': '15px'}),
                                    dcc.RadioItems(
                                        id='insight-mode-radio',
                                        options=[
                                            {'label': 'Individual Insights', 'value': 'individual'},
                                            {'label': 'Combined Insights', 'value': 'combined'},
                                        ],
                                        value='individual',
                                        labelStyle={'display': 'block', 'marginTop': '5px'}
                                    ),
                                ], style={'marginTop': '10px'}),

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
                                html.Div(id='generate-output'),
                            ],
                            style={
                                'padding': '16px 20px 40px',
                                'backgroundColor': '#f8f9fa',
                                'display': 'flex', 'flexDirection': 'column',
                                'gap': '6px',
                                'height': '100%', 'minHeight': 0,
                                'overflowY': 'auto', 'overflowX': 'hidden',
                                'WebkitOverflowScrolling': 'touch', 'overscrollBehavior': 'contain',
                                'boxSizing': 'border-box'
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
                # First open at 25% of the screen width
                panel_style = {'height': '100vh', 'backgroundColor': '#f8f9fa', 'width': '25%'}
                new_store = {'visible': True, 'opened_once': True}
            else:
                panel_style = {'height': '100vh', 'backgroundColor': '#f8f9fa'}
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
        State('insight-mode-radio', 'value'),
        prevent_initial_call=True
    )
    def generate_report(n_clicks, selected_graphs, selected_data, filters, insight_mode):
        if not n_clicks:
            return ""
        if not selected_graphs:
            return html.Div([
                html.H4("No charts selected.", style={'color': '#991B1B'}),
                html.P("Use “Select this graph” under one or more charts.")
            ])

        def label(gid):
            return GRAPH_LABELS.get(gid, gid)

        # Backward compatibility: prefer full data; fall back to legacy or chart
        def pick_meta(meta_obj):
            if not isinstance(meta_obj, dict):
                return None
            # legacy flat structure
            if "columns" in meta_obj and "records" in meta_obj:
                return meta_obj
            # prefer full, then chart
            if 'full' in meta_obj and isinstance(meta_obj['full'], dict):
                return meta_obj['full']
            if 'chart' in meta_obj and isinstance(meta_obj['chart'], dict):
                return meta_obj['chart']
            return None

        charts_payload = []
        for gid in selected_graphs:
            meta_all = (selected_data or {}).get(gid)
            meta = pick_meta(meta_all)
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

        prompt_individual = (
            "You are a data analyst. I will provide multiple chart datasets as JSON.\n"
            "Return plain markdown only (no code fences). Be specific and data-driven.\n"
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

        prompt_combined = (
            "You are a senior data analyst. I will provide datasets for multiple charts as JSON.\n"
            "Return plain markdown only (no code fences). Synthesize the data across charts.\n"
            "Instead of analyzing each chart in isolation, focus on the connections, correlations, and combined story they tell.\n\n"
            "Provide your analysis in concise markdown with the following structure:\n"
            "### Overall Summary\n"
            "- A brief, high-level summary of the key findings from all charts combined (2-3 sentences).\n"
            "### Cross-Chart Insights\n"
            "- 3-5 bullet points identifying trends, correlations, or discrepancies *between* the different datasets.\n"
            "### Key Outliers or Notables\n"
            "- Mention any significant outliers or data points that stand out when considering the data as a whole.\n"
            "### Strategic Recommendation\n"
            "- Based on your combined analysis, provide one actionable strategic suggestion.\n\n"
            "JSON data follows:\n```json\n"
            + json.dumps(payload, ensure_ascii=False)
            + "\n```"
        )

        prompt = prompt_combined if insight_mode == 'combined' else prompt_individual

        llm_text, err = generate_markdown_from_prompt(prompt, model_name=MODEL_NAME, api_key=GOOGLE_API_KEY)
        if err:
            return html.Div([
                html.H4("Error Generating Report", style={'color': '#991B1B'}),
                html.P(f"LLM error: {err}")
            ])

        # Some models wrap the entire response in triple backticks, causing it to
        # render as a code block instead of markdown. Strip a single outer fence.
        def _unwrap_code_fence(s: str | None) -> str:
            if not s:
                return ""
            text = s.strip()
            m = re.match(r"^```(?:[a-zA-Z0-9_-]+)?\s*\n(.*)\n```$", text, flags=re.S)
            if m:
                return m.group(1).strip()
            # Fallback: leading fence only
            if text.startswith("```") and text.count("```") >= 2:
                first_close = text.find("```", 3)
                if first_close != -1:
                    inner = text[3:first_close]
                    rest = text[first_close+3:].strip()
                    if not rest:
                        return inner.strip()
            return text

        cleaned = _unwrap_code_fence(llm_text)

        # ---- Evidence Panel (render chosen scope for alignment) ----
        def evidence_table(meta):
            cols = [{"name": str(c), "id": str(c)} for c in (meta.get('columns') or [])]
            data = list(meta.get('records') or [])
            return dash_table.DataTable(
                columns=cols,
                data=data,
                page_size=10,
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto', 'marginTop': '6px', 'maxHeight': '40vh', 'overflowY': 'auto', 'border': '1px solid #e5e7eb', 'borderRadius': '8px'},
                style_cell={'fontFamily': 'Roboto, sans-serif', 'fontSize': 12, 'padding': '8px', 'whiteSpace': 'normal', 'height': 'auto', 'textAlign': 'left'},
                style_header={'fontWeight': 'bold', 'backgroundColor': '#f3f4f6', 'borderBottom': '1px solid #e5e7eb'},
                style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#fafafa'}],
                fixed_rows={'headers': True},
                style_as_list_view=True,
            )

        ev_sections = []
        for gid in selected_graphs:
            meta_all = (selected_data or {}).get(gid) or {}
            meta = pick_meta(meta_all)
            if not meta:
                continue
            ev_sections.append(
                html.Details([
                    html.Summary(f"{label(gid)} — Full data — {meta.get('n_rows', 0)} rows"),
                    evidence_table(meta)
                ], open=False, style={'marginTop': '8px'})
            )

        evidence = html.Div([
            html.Hr(),
            html.H4("Evidence Review", style={'color': '#374151'}),
            html.P("Data used for the analysis (limited preview).", style={'color': '#6b7280', 'fontSize': '12px'}),
            html.Div(ev_sections)
        ])

        return html.Div([
            html.H4("Generated Report", style={'color': '#007bff'}),
            dcc.Markdown(cleaned or "_No content returned._", link_target="_blank"),
            evidence
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
        Input('t2-graph-q1', 'clickData'),
        Input('t2-graph-q2', 'clickData'),
        Input('t2-graph-q3', 'clickData'),
        Input('t2-graph-q4a', 'clickData'),
        Input('t2-graph-q4b', 'clickData'),
        # Tab 3 clicks should also update global filters where applicable
        Input('t3-graph-1', 'clickData'),
        Input('t3-graph-2', 'clickData'),
        Input('t3-graph-3', 'clickData'),
        Input('t3-graph-4', 'clickData'),
        Input('t3-graph-5', 'clickData'),

        State('filter-store', 'data'),
        State('active-selection', 'data'),
        prevent_initial_call=True
    )
    def update_filters_and_ui(
        reset_clicks, weeks, outlet_cats, regions, customer_cats,
        click_q1, click_q2, click_q3, click_q4, click_q5,
        click_t2_q1, click_t2_q2, click_t2_q3, click_t2_q4a, click_t2_q4b,
        click_t3_g1, click_t3_g2, click_t3_g3, click_t3_g4, click_t3_g5,
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

        def make_key_t2(graph_id, point):
            def _cd(p, i=0, default=None):
                try:
                    return p.get('customdata', [default])[i]
                except Exception:
                    return default

            if graph_id == 't2-graph-q1':
                return f"t2q1|week={point['x']}"
            if graph_id == 't2-graph-q2':
                return f"t2q2|week={point['x']}|outlet={_cd(point)}"
            if graph_id == 't2-graph-q3':
                # heatmap: x=service_type, y=outlet_category
                return f"t2q3|service={point['x']}|outlet={point['y']}"
            if graph_id == 't2-graph-q4a':
                return f"t2q4a|label={point.get('y')}"
            if graph_id == 't2-graph-q4b':
                return f"t2q4b|state={point['x']}|region={_cd(point)}"
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

        if trig_id.startswith('t2-graph-') and trig.get('value'):
            point = trig['value']['points'][0]
            key = make_key_t2(trig_id, point)

            if active_selection == key:
                return default_filters, None, [], [], [], []

            new_filters = default_filters.copy()

            if trig_id == 't2-graph-q1':
                new_filters['weeks'] = [point['x']]
            elif trig_id == 't2-graph-q2':
                new_filters['weeks'] = [point['x']]
                oc = None
                try:
                    oc = point['customdata'][0]
                except Exception:
                    pass
                if oc:
                    new_filters['outlet_categories'] = [oc]
            elif trig_id == 't2-graph-q3':
                new_filters['service_types'] = [point['x']]
                new_filters['outlet_categories'] = [point['y']]
            elif trig_id == 't2-graph-q4a':
                # Efficiency ranking: use outlet_category from customdata to drive global category filter
                try:
                    oc = point.get('customdata', [None])[0]
                except Exception:
                    oc = None
                if oc:
                    new_filters['outlet_categories'] = [oc]
            elif trig_id == 't2-graph-q4b':
                new_filters['states'] = [point['x']]
                try:
                    reg = point['customdata'][0]
                    if reg:
                        new_filters['regions'] = [reg]
                except Exception:
                    pass

            return (new_filters, key, new_filters.get('weeks', []),
                    new_filters.get('outlet_categories', []),
                    new_filters.get('regions', []),
                    new_filters.get('customer_categories', []))

        # Tab 3 -> Global filters (only where dimensions match the global filter bar)
        if trig_id.startswith('t3-graph-') and trig.get('value'):
            point = trig['value']['points'][0]

            # Only propagate weeks and outlet_category; ignore tiers/centers at global level
            new_filters = default_filters.copy()
            key = None
            if trig_id == 't3-graph-1':
                # Expect x = week_number and customdata [week, outlet_category]
                if 'x' in point:
                    new_filters['weeks'] = [point['x']]
                cd = point.get('customdata') or []
                if len(cd) > 1 and cd[1]:
                    new_filters['outlet_categories'] = [cd[1]]
                key = f"t3g1|week={point.get('x')}|outlet={(cd[1] if len(cd)>1 else None)}"
            elif trig_id == 't3-graph-2':
                cd = point.get('customdata') or []
                if cd:
                    new_filters['outlet_categories'] = [cd[0]]
                key = f"t3g2|outlet={(cd[0] if cd else None)}"
            elif trig_id == 't3-graph-3':
                # Tier has no global control; keep current filters
                return (current_filters, active_selection, current_filters.get('weeks', []),
                        current_filters.get('outlet_categories', []), current_filters.get('regions', []),
                        current_filters.get('customer_categories', []))
            elif trig_id in ('t3-graph-4', 't3-graph-5'):
                # Center code has no global control; keep current filters
                return (current_filters, active_selection, current_filters.get('weeks', []),
                        current_filters.get('outlet_categories', []), current_filters.get('regions', []),
                        current_filters.get('customer_categories', []))

            # If user clicks the same again, clear global filters
            if active_selection == key:
                return default_filters, None, [], [], [], []

            return (new_filters, key, new_filters.get('weeks', []),
                    new_filters.get('outlet_categories', []),
                    new_filters.get('regions', []),
                    new_filters.get('customer_categories', []))

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

            return (new_filters, key, new_filters.get('weeks', []),
                    new_filters.get('outlet_categories', []),
                    new_filters.get('regions', []),
                    new_filters.get('customer_categories', []))

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
        return build_tab1_figures(
            data_dict,
            filters,
            all_outlet_categories,
            all_regions,
            outlet_color_map,
            region_color_map,
            base_palette,
            GRAPH_LABELS,
        )

    # ----- Multi-select buttons: capture selections & store snapshots -----
    @app.callback(
        Output('selected-graphs', 'data'),
        Output('selected-data', 'data'),
        Output('selected-info', 'children'),
        # Tab 1 buttons
        Input('btn-select-q1', 'n_clicks'),
        Input('btn-select-q2', 'n_clicks'),
        Input('btn-select-q3', 'n_clicks'),
        Input('btn-select-q4', 'n_clicks'),
        Input('btn-select-q5', 'n_clicks'),
        # Tab 2 buttons
        Input('btn-select-t2-q1', 'n_clicks'),
        Input('btn-select-t2-q2', 'n_clicks'),
        Input('btn-select-t2-q3', 'n_clicks'),
        Input('btn-select-t2-q4a', 'n_clicks'),
        Input('btn-select-t2-q4b', 'n_clicks'),
        # Tab 3 buttons
        Input('btn-select-t3-1', 'n_clicks'),
        Input('btn-select-t3-2', 'n_clicks'),
        Input('btn-select-t3-3', 'n_clicks'),
        Input('btn-select-t3-4', 'n_clicks'),
        Input('btn-select-t3-5', 'n_clicks'),
        # Clear selection button in sidebar
        Input('clear-selection', 'n_clicks'),
        # States
        State('filter-store', 'data'),
        State('tab3-filter-store', 'data'),
        State('selected-graphs', 'data'),
        State('selected-data', 'data'),
        prevent_initial_call=True
    )
    def handle_select(*args):
        (
            btn1, btn2, btn3, btn4, btn5,
            t2b1, t2b2, t2b3, t2b4a, t2b4b,
            t3b1, t3b2, t3b3, t3b4, t3b5,
            clear_btn,
            filters, tab3_local, selected_graphs, selected_data
        ) = args
        triggered = ctx.triggered_id
        if triggered is None:
            raise PreventUpdate

        selected_graphs = list(selected_graphs or [])
        selected_data = dict(selected_data or {})

        # Clear selection request from sidebar
        if triggered == 'clear-selection':
            info = html.Div("No charts selected yet.", style={'color': '#6b7280', 'fontSize': '13px'})
            return [], {}, info

        # Helper to add/remove
        def toggle(graph_id: str, df_full, df_chart):
            nonlocal selected_graphs, selected_data
            if graph_id in selected_graphs:
                selected_graphs = [g for g in selected_graphs if g != graph_id]
                selected_data.pop(graph_id, None)
            else:
                selected_graphs.append(graph_id)
                selected_data[graph_id] = {
                    'full': pack_df(df_full),
                    'chart': pack_df(df_chart),
                }

        # Tab 1 mapping (store UNFILTERED datasets for LLM)
        if triggered.startswith('btn-select-q'):
            # Build both full (unfiltered) and chart (current-filtered) datasets
            df_q1_full, df_q2_full, df_q3_full, df_q4_full, df_q5_full = t1_get_filtered_frames(data_dict, {})
            df_q1_chart, df_q2_chart, df_q3_chart, df_q4_chart, df_q5_chart = t1_get_filtered_frames(data_dict, filters or {})
            id_map = {
                'btn-select-q1': ('q1', df_q1_full, df_q1_chart),
                'btn-select-q2': ('q2', df_q2_full, df_q2_chart),
                'btn-select-q3': ('q3', df_q3_full, df_q3_chart),
                'btn-select-q4': ('q4', df_q4_full, df_q4_chart),
                'btn-select-q5': ('q5', df_q5_full, df_q5_chart),
            }
            gid, df_full, df_chart = id_map[triggered]
            toggle(gid, df_full, df_chart)
        # Tab 2 mapping (store UNFILTERED datasets for LLM)
        elif triggered.startswith('btn-select-t2-'):
            # Build both full (unfiltered) and chart (current-filtered) datasets
            q1_t2_full, q2_t2_full, q3_t2_full, q4_t2_full = t2_get_filtered_frames(tab2, {})
            q1_t2_chart, q2_t2_chart, q3_t2_chart, q4_t2_chart = t2_get_filtered_frames(tab2, filters or {})
            id_map2 = {
                'btn-select-t2-q1': ('t2-graph-q1', q1_t2_full, q1_t2_chart),
                'btn-select-t2-q2': ('t2-graph-q2', q2_t2_full, q2_t2_chart),
                'btn-select-t2-q3': ('t2-graph-q3', q3_t2_full, q3_t2_chart),
                'btn-select-t2-q4a': ('t2-graph-q4a', q4_t2_full, q4_t2_chart),
                'btn-select-t2-q4b': ('t2-graph-q4b', q4_t2_full, q4_t2_chart),
            }
            gid, df_full, df_chart = id_map2[triggered]
            toggle(gid, df_full, df_chart)
        # Tab 3 mapping (store UNFILTERED datasets for LLM)
        else:
            # Build both full (unfiltered) and chart (global+local filtered) datasets
            q1_t3_full, q2_t3_full, q3_t3_full, q4_t3_full = t3_get_filtered_frames(data_dict_3 or {}, {})
            m_t3_full = merged_for_chart2(q2_t3_full, q3_t3_full)

            # Merge global and local filters for chart scope
            gf = filters or {}
            lf = tab3_local or {}
            def combine(a, b):
                la = list(a or [])
                lb = list(b or [])
                if la and lb:
                    sb = set(lb)
                    return [x for x in la if x in sb]
                return la or lb
            merged = {
                'weeks': combine(gf.get('weeks'), lf.get('weeks')),
                'outlet_categories': combine(gf.get('outlet_categories'), lf.get('outlet_categories')),
                'performance_tiers': list(lf.get('performance_tiers', [])),
                'sales_center_codes': list(lf.get('sales_center_codes', [])),
                'service_types': list(gf.get('service_types', [])),
                'regions': list(gf.get('regions', [])),
                'states': list(gf.get('states', [])),
            }
            q1_t3_chart, q2_t3_chart, q3_t3_chart, q4_t3_chart = t3_get_filtered_frames(data_dict_3 or {}, merged)
            m_t3_chart = merged_for_chart2(q2_t3_chart, q3_t3_chart)
            id_map3 = {
                'btn-select-t3-1': ('t3-graph-1', q2_t3_full, q2_t3_chart),
                'btn-select-t3-2': ('t3-graph-2', m_t3_full, m_t3_chart),
                'btn-select-t3-3': ('t3-graph-3', q3_t3_full, q3_t3_chart),
                'btn-select-t3-4': ('t3-graph-4', q3_t3_full, q3_t3_chart),
                'btn-select-t3-5': ('t3-graph-5', q4_t3_full, q4_t3_chart),
            }
            gid, df_full, df_chart = id_map3[triggered]
            toggle(gid, df_full, df_chart)

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

    # ----- View-underlying-data tables (inline) -----
    @app.callback(
        # Tab 1 tables
        Output('table-q1', 'children'),
        Output('table-q2', 'children'),
        Output('table-q3', 'children'),
        Output('table-q4', 'children'),
        Output('table-q5', 'children'),
        # Tab 2 tables
        Output('table-t2-q1', 'children'),
        Output('table-t2-q2', 'children'),
        Output('table-t2-q3', 'children'),
        Output('table-t2-q4a', 'children'),
        Output('table-t2-q4b', 'children'),
        # Tab 3 tables
        Output('table-t3-1', 'children'),
        Output('table-t3-2', 'children'),
        Output('table-t3-3', 'children'),
        Output('table-t3-4', 'children'),
        Output('table-t3-5', 'children'),

        # Inputs: all view buttons
        Input('btn-view-q1', 'n_clicks'),
        Input('btn-view-q2', 'n_clicks'),
        Input('btn-view-q3', 'n_clicks'),
        Input('btn-view-q4', 'n_clicks'),
        Input('btn-view-q5', 'n_clicks'),
        Input('btn-view-t2-q1', 'n_clicks'),
        Input('btn-view-t2-q2', 'n_clicks'),
        Input('btn-view-t2-q3', 'n_clicks'),
        Input('btn-view-t2-q4a', 'n_clicks'),
        Input('btn-view-t2-q4b', 'n_clicks'),
        Input('btn-view-t3-1', 'n_clicks'),
        Input('btn-view-t3-2', 'n_clicks'),
        Input('btn-view-t3-3', 'n_clicks'),
        Input('btn-view-t3-4', 'n_clicks'),
        Input('btn-view-t3-5', 'n_clicks'),

        # States: filters
        State('filter-store', 'data'),
        State('tab3-filter-store', 'data'),
        # States: current table contents for toggling
        State('table-q1', 'children'),
        State('table-q2', 'children'),
        State('table-q3', 'children'),
        State('table-q4', 'children'),
        State('table-q5', 'children'),
        State('table-t2-q1', 'children'),
        State('table-t2-q2', 'children'),
        State('table-t2-q3', 'children'),
        State('table-t2-q4a', 'children'),
        State('table-t2-q4b', 'children'),
        State('table-t3-1', 'children'),
        State('table-t3-2', 'children'),
        State('table-t3-3', 'children'),
        State('table-t3-4', 'children'),
        State('table-t3-5', 'children'),
        prevent_initial_call=True
    )
    def show_underlying_tables(
        vq1, vq2, vq3, vq4, vq5,
        vt2q1, vt2q2, vt2q3, vt2q4a, vt2q4b,
        vt3_1, vt3_2, vt3_3, vt3_4, vt3_5,
        filters, tab3_local,
        tq1, tq2, tq3, tq4, tq5,
        tt2q1, tt2q2, tt2q3, tt2q4a, tt2q4b,
        tt3_1, tt3_2, tt3_3, tt3_4, tt3_5
    ):
        triggered = ctx.triggered_id
        if triggered is None:
            raise PreventUpdate

        # Helper: build a DataTable from a DataFrame
        def table_from_df(df):
            import pandas as pd  # local import to avoid global dependency if not used elsewhere
            if df is None or isinstance(df, pd.DataFrame) and df.empty:
                return html.Div("No data to display.", style={'color': '#6b7280', 'fontSize': '13px', 'marginTop': '6px'})
            # Limit rows for UI responsiveness
            try:
                df = df.head(300)
            except Exception:
                pass
            columns = [{"name": str(c), "id": str(c)} for c in df.columns]
            return dash_table.DataTable(
                columns=columns,
                data=df.to_dict('records'),
                page_size=10,
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto', 'marginTop': '6px', 'maxHeight': '50vh', 'overflowY': 'auto', 'border': '1px solid #e5e7eb', 'borderRadius': '8px'},
                style_cell={'fontFamily': 'Roboto, sans-serif', 'fontSize': 12, 'padding': '8px', 'whiteSpace': 'normal', 'height': 'auto', 'textAlign': 'left'},
                style_header={'fontWeight': 'bold', 'backgroundColor': '#f3f4f6', 'borderBottom': '1px solid #e5e7eb'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#fafafa'},
                ],
                fixed_rows={'headers': True},
                style_as_list_view=True,
            )

        # Defaults: no update for all outputs
        out = [no_update] * 15

        # Resolve filtered frames based on which section triggered
        if triggered.startswith('btn-view-q'):
            # Tab 1 filtered frames (include plotted variants)
            df_q1, df_q2_plot, df_q3_plot, df_q4_plot, df_q5_plot = t1_get_filtered_frames(data_dict, filters or {})
            id_map = {
                'btn-view-q1': (0, df_q1, tq1),
                'btn-view-q2': (1, df_q2_plot, tq2),
                'btn-view-q3': (2, df_q3_plot, tq3),
                'btn-view-q4': (3, df_q4_plot, tq4),
                'btn-view-q5': (4, df_q5_plot, tq5),
            }
            idx, df, cur = id_map[triggered]
            out[idx] = None if cur else table_from_df(df)
        elif triggered.startswith('btn-view-t2-'):
            # Tab 2 filtered frames (long-form datasets)
            q1_t2, q2_t2, q3_t2, q4_t2 = t2_get_filtered_frames(tab2, filters or {})
            id_map2 = {
                'btn-view-t2-q1': (5, q1_t2, tt2q1),
                'btn-view-t2-q2': (6, q2_t2, tt2q2),
                'btn-view-t2-q3': (7, q3_t2, tt2q3),
                'btn-view-t2-q4a': (8, q4_t2, tt2q4a),
                'btn-view-t2-q4b': (9, q4_t2, tt2q4b),
            }
            idx, df, cur = id_map2[triggered]
            out[idx] = None if cur else table_from_df(df)
        else:
            # Tab 3: merge global + local filters similar to other callbacks
            gf = filters or {}
            lf = tab3_local or {}
            def combine(a, b):
                la = list(a or [])
                lb = list(b or [])
                if la and lb:
                    sb = set(lb)
                    return [x for x in la if x in sb]
                return la or lb
            merged = {
                'weeks': combine(gf.get('weeks'), lf.get('weeks')),
                'outlet_categories': combine(gf.get('outlet_categories'), lf.get('outlet_categories')),
                'performance_tiers': list(lf.get('performance_tiers', [])),
                'sales_center_codes': list(lf.get('sales_center_codes', [])),
                'service_types': list(gf.get('service_types', [])),
                'regions': list(gf.get('regions', [])),
                'states': list(gf.get('states', [])),
            }
            q1_t3, q2_t3, q3_t3, q4_t3 = t3_get_filtered_frames(data_dict_3 or {}, merged)
            m_t3 = merged_for_chart2(q2_t3, q3_t3)
            id_map3 = {
                'btn-view-t3-1': (10, q2_t3, tt3_1),
                'btn-view-t3-2': (11, m_t3, tt3_2),
                'btn-view-t3-3': (12, q3_t3, tt3_3),
                'btn-view-t3-4': (13, q3_t3, tt3_4),
                'btn-view-t3-5': (14, q4_t3, tt3_5),
            }
            idx, df, cur = id_map3[triggered]
            out[idx] = None if cur else table_from_df(df)

        return tuple(out)

    # ----- Tab 2: figures (q1–q4b) -----
    @app.callback(
        Output('t2-graph-q1', 'figure'),
        Output('t2-graph-q2', 'figure'),
        Output('t2-graph-q3', 'figure'),
        Output('t2-graph-q4a', 'figure'),
        Output('t2-graph-q4b', 'figure'),
        Input('filter-store', 'data')
    )
    def update_tab2_figures(filters):
        return build_tab2_figures(
            tab2,
            filters,
            outlet_color_map=outlet_color_map,
            region_color_map=region_color_map,
            all_outlet_categories=all_outlet_categories,
            all_regions=all_regions,
            labels=GRAPH_LABELS,
        )

    # ----- Tab 3: Five-Chart Dashboard figures -----
    @app.callback(
        Output('t3-graph-1', 'figure'),
        Output('t3-graph-2', 'figure'),
        Output('t3-graph-3', 'figure'),
        Output('t3-graph-4', 'figure'),
        Output('t3-graph-5', 'figure'),
        Input('filter-store', 'data'),
        Input('tab3-filter-store', 'data')
    )
    def update_tab3_figures(global_filters, local_filters):
        # Merge global and local filters: apply both (intersection when both present)
        gf = global_filters or {}
        lf = local_filters or {}

        def combine(a, b):
            la = list(a or [])
            lb = list(b or [])
            if la and lb:
                sb = set(lb)
                return [x for x in la if x in sb]
            return la or lb

        merged = {
            'weeks': combine(gf.get('weeks'), lf.get('weeks')),
            'outlet_categories': combine(gf.get('outlet_categories'), lf.get('outlet_categories')),
            'performance_tiers': list(lf.get('performance_tiers', [])),
            'sales_center_codes': list(lf.get('sales_center_codes', [])),
            # pass-through global-only filters as well
            'service_types': list(gf.get('service_types', [])),
            'regions': list(gf.get('regions', [])),
            'states': list(gf.get('states', [])),
        }
        return build_tab3_figures(
            data_dict_3 or {},
            merged,
            outlet_color_map=outlet_color_map,
            tier_colors=tier_color_map(),
            all_outlet_categories=all_outlet_categories,
            labels=GRAPH_LABELS,
        )

    # Tab 3 cross-filtering controller
    @app.callback(
        Output('tab3-filter-store', 'data'),
        Input('t3-graph-1', 'clickData'),
        Input('t3-graph-2', 'clickData'),
        Input('t3-graph-3', 'clickData'),
        Input('t3-graph-4', 'clickData'),
        Input('t3-graph-5', 'clickData'),
        State('tab3-filter-store', 'data'),
        prevent_initial_call=True
    )
    def update_tab3_filters(c1, c2, c3, c4, c5, current):
        current = dict(current or {'weeks': [], 'outlet_categories': [], 'performance_tiers': [], 'sales_center_codes': []})
        trig_id = ctx.triggered_id
        if trig_id is None:
            raise PreventUpdate
        newf = current.copy()

        def get_first_point(click):
            try:
                return (click or {}).get('points', [{}])[0]
            except Exception:
                return None

        def toggle_single(cur_list, val):
            cur = list(cur_list or [])
            if val is None:
                return cur
            return [] if (len(cur) == 1 and cur[0] == val) else [val]

        if trig_id == 't3-graph-1':
            point = get_first_point(c1)
            if point:
                if 'x' in point:
                    newf['weeks'] = toggle_single(newf.get('weeks'), point['x'])
                cd = point.get('customdata') or []
                if cd:
                    # expecting [week_number, outlet_category]
                    if len(cd) > 1 and cd[1]:
                        newf['outlet_categories'] = toggle_single(newf.get('outlet_categories'), cd[1])
        elif trig_id == 't3-graph-2':
            point = get_first_point(c2)
            if point:
                cd = point.get('customdata') or []
                if cd:
                    newf['outlet_categories'] = toggle_single(newf.get('outlet_categories'), cd[0])
        elif trig_id == 't3-graph-3':
            point = get_first_point(c3)
            if point:
                cd = point.get('customdata') or []
                tier = cd[0] if cd else (point.get('legendgroup') or point.get('label') or point.get('x'))
                if tier:
                    newf['performance_tiers'] = toggle_single(newf.get('performance_tiers'), tier)
        elif trig_id == 't3-graph-4':
            point = get_first_point(c4)
            if point:
                cd = point.get('customdata') or []
                code = cd[0] if cd else None
                if code is not None:
                    newf['sales_center_codes'] = toggle_single(newf.get('sales_center_codes'), str(code))
        elif trig_id == 't3-graph-5':
            point = get_first_point(c5)
            if point:
                code = None
                cd = point.get('customdata') or []
                if cd:
                    code = cd[0]
                if code is None:
                    # fallbacks for bar chart
                    code = point.get('y') or point.get('label') or point.get('x')
                if code is not None:
                    newf['sales_center_codes'] = toggle_single(newf.get('sales_center_codes'), str(code))
        return newf

    return app


if __name__ == '__main__':
    try:
        data_dict = get_tab1_results()
        data_dict_tab2 = get_tab2_results()
        data_dict_tab3 = get_tab3_results()
        app = create_dashboard(data_dict, data_dict_tab2, data_dict_tab3)
        app.run(debug=True, port=8090)
    except ImportError:
        print("Error: Could not import 'get_tab1_results' from 'data_layer.tab_1'.")
        print("Please ensure the file exists and the 'src' directory is in your Python path.")
    except Exception as e:
        print(f"An error occurred during app setup: {e}")
