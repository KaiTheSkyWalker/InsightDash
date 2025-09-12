import dash
import re
from dash import dcc, html, Input, Output, State, ctx, no_update
from dash import dash_table
from dash.exceptions import PreventUpdate
import pandas as pd
import json
from dash_resizable_panels import PanelGroup, Panel, PanelResizeHandle
import os


from data_layer.tab_1 import get_tab1_results
from data_layer.tab_2 import get_tab2_results
from data_layer.tab_3 import get_tab3_results
from config.settings import GOOGLE_API_KEY, MODEL_NAME
from services.llm import generate_markdown_from_prompt, generate_markdown_openrouter
from services.prompts import build_prompt_individual
from utils.data import uniq, pack_df
from utils.colors import (
    color_map_from_list,
    tier_color_map,
    diverse_palette,
    base_palette,
)
import plotly.io as pio
from app_tabs.tab1.layout import get_layout as tab1_layout
from app_tabs.tab2.layout import get_layout as tab2_layout
from app_tabs.tab3.layout import get_layout as tab3_layout
from app_tabs.tab1.figures import (
    get_filtered_frames as t1_get_filtered_frames,
    build_tab1_figures,
)

# legacy build_tab2_figures unused; Tab 2 now uses dynamic scatter only
from app_tabs.tab3.figures import (
    build_tab3_figures,
    get_filtered_frames_simple as t3_get_filtered_frames,
    KPI_DISPLAY,
)
from app_tabs.tab2.figures import get_filtered_frames as t2_get_filtered_frames
from config.logging import configure_logging

# Configure logging early so all modules use the same sink
configure_logging()

"""
Configuration and LLM are now centralized in config.settings and services.llm.
MODEL_NAME and GOOGLE_API_KEY are imported from settings.
"""


# ---------- Fonts / styles ----------
# Use Google Fonts via external stylesheet. You can adjust the family below.
external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
]


def _ensure_tab1_defaults(data_dict: dict | None) -> dict:
    """Ensure Tab 1 dict has q1..q5 DataFrames with required columns.

    Prevents KeyError in layouts when DB is unavailable by providing
    empty frames with the expected schema.
    """
    d = dict(data_dict or {})

    def ensure_df(df, cols):
        if isinstance(df, pd.DataFrame):
            out = df.copy()
            for c in cols:
                if c not in out.columns:
                    out[c] = None
            return out
        return pd.DataFrame(columns=cols)

    # Align to sql_queries.sheet1 output columns
    return {
        "q1": ensure_df(
            d.get("q1"),
            [
                "rgn",
                "outlet_category",
                "sales_outlet",
                "rate_performance",
                "rate_quality",
                "total_score",
            ],
        ),
        "q2": ensure_df(
            d.get("q2"),
            [
                "outlet_category",
                "avg_total_score",
                "avg_new_car_reg",
                "avg_intake_units",
                "avg_revenue_performance",
            ],
        ),
        "q3": ensure_df(
            d.get("q3"),
            [
                "rgn",
                "outlet_category",
                "outlet_count",
                "avg_total_score",
                "avg_national_rank",
                "avg_regional_rank",
            ],
        ),
        "q4": ensure_df(
            d.get("q4"),
            [
                "sales_outlet",
                "rgn",
                "outlet_category",
                "total_score",
                "rank_nationwide",
                "rank_region",
                "new_car_reg_unit",
                "intake_unit",
                "revenue_pct",
            ],
        ),
        "q5": ensure_df(
            d.get("q5"),
            [
                "sales_outlet",
                "rgn",
                "outlet_category",
                "total_score",
                "rank_nationwide",
                "rank_region",
                "new_car_reg_unit",
                "intake_unit",
                "revenue_pct",
            ],
        ),
    }


def create_dashboard(data_dict, data_dict_2, data_dict_3=None):
    """
    Dash app with cross-filtering, stable colors, multi-chart select,
    and Gemini-based summarizer in a resizable, toggleable sidebar.
    """
    # local aliases for datasets (prevents NameError in inner functions)
    tab1 = _ensure_tab1_defaults(data_dict or {})
    tab2 = data_dict_2 or {}

    app = dash.Dash(
        __name__,
        suppress_callback_exceptions=True,
        external_stylesheets=external_stylesheets,
    )

    # Set a consistent blue-forward plotly template across all figures
    pio.templates.default = "plotly_white"

    # Helpers moved to utils.data and utils.colors

    # ----- Data & filters -----
    all_outlet_categories = sorted(
        uniq(
            [
                tab1.get("q2", pd.DataFrame()).get("outlet_category"),
                tab1.get("q3", pd.DataFrame()).get("outlet_category"),
                tab1.get("q4", pd.DataFrame()).get("outlet_category"),
                tab1.get("q5", pd.DataFrame()).get("outlet_category"),
            ]
        )
    )
    # Fallback: derive from Tab 2 dataset, else default A/B/C/D
    if not all_outlet_categories:
        try:
            s = (data_dict_2 or {}).get("q1", pd.DataFrame()).get("outlet_category")
            if s is not None:
                all_outlet_categories = sorted(pd.Index(s.dropna().unique()).tolist())
        except Exception:
            pass
    if not all_outlet_categories:
        all_outlet_categories = ["A", "B", "C", "D"]

    all_regions = sorted(
        uniq(
            [
                tab1.get("q1", pd.DataFrame()).get("rgn"),
                tab1.get("q3", pd.DataFrame()).get("rgn"),
                tab1.get("q4", pd.DataFrame()).get("rgn"),
                tab1.get("q5", pd.DataFrame()).get("rgn"),
            ]
        )
    )

    outlet_color_map = color_map_from_list(all_outlet_categories)
    scatter_color_map = color_map_from_list(
        all_outlet_categories, palette=diverse_palette
    )
    region_color_map = color_map_from_list(all_regions)

    # Derive all outlet types and KPI columns from available datasets (sheet2.q1, sheet3.q1)
    df_t2_q1 = (data_dict_2 or {}).get("q1", pd.DataFrame())
    df_t3_q1 = (data_dict_3 or {}).get("q1", pd.DataFrame())

    def safe_unique(series_like):
        try:
            return sorted(
                [
                    x
                    for x in pd.Index(series_like).dropna().unique().tolist()
                    if x is not None
                ]
            )
        except Exception:
            return []

    all_outlet_types = safe_unique(df_t2_q1.get("outlet_type", pd.Series(dtype=object)))
    if not all_outlet_types:
        all_outlet_types = safe_unique(
            df_t3_q1.get("outlet_type", pd.Series(dtype=object))
        )

    # KPI columns in sheet2/3 (achievement %)
    # Removed unused KPI_COLUMNS constant in cleanup.

    # Default filters implement the pasted rules (global slicers)
    default_filters = {
        "outlet_categories": [],  # A/B/C/D
        "regions": [],  # rgn
        "outlet_types": [],  # outlet_type
        "outlets": [],  # specific outlet(s)
        "search_text": "",  # outlet_name search (UI removed)
        # Legacy controls retained
        "score_band": "All",
        "units_band": "All",
        # KPI selector
        "kpi_group": "All",  # All | Performance | Quality
        "kpi_single": None,  # specific KPI column name
    }

    GRAPH_LABELS = {
        # Tab 1 (Overview)
        "q1": "Average Total Score by Region",
        "q2": "Outlet Category Distribution (% by Region)",
        "q3": "Performance vs. Quality by Region",
        "q4": "Top Outlets by Score",
        "q5": "Bottom Outlets by Score",
        "q6": "Number of Outlets by Category",
        # Tab 2 (Operational Insights)
        "t2-graph-q1": "Sales vs. Service Performance Quadrant",
        "t2-graph-q2": "After-Sales Revenue Composition by Outlet (Top 20)",
        "t2-graph-q3": "Outlets with the Largest Sales–Service Gap",
        "t2-graph-q4a": "Insurance Renewal Rates",
        "t2-graph-q4b": "KPI Correlation (Pearson)",
        "t2-graph-dyn": "Explore Parameter Relationships",
        # Tab 3 (Performance Analyzer)
        "t3-graph-1": "What's Holding Back B, C, & D Outlets?",
        "t3-graph-2": "Average Performance Profile by Outlet Type",
        "t3-graph-3": "Outlet Spread within Selected Category",
        "t3-graph-4": "—",
        # 't3-graph-5': '—',
    }

    # ----- Layout -----
    app.layout = html.Div(
        [
            PanelGroup(
                id="main-panel-group",
                direction="horizontal",
                autoSaveId="vrdb-split",  # persist widths
                style={"height": "100dvh", "minHeight": 0},
                children=[
                    # Main Content Panel
                    Panel(
                        id="main-panel",
                        children=[
                            html.Div(
                                id="main-content",
                                children=[
                                    html.Div(
                                        [
                                            html.H1(
                                                "Perodua CR KPI Dashboard",
                                                style={
                                                    "textAlign": "center",
                                                    "flex": "1",
                                                },
                                            ),
                                            html.Button(
                                                "☰",
                                                id="sidebar-toggle-button",
                                                n_clicks=0,
                                                style={
                                                    "height": "36px",
                                                    "marginLeft": "20px",
                                                },
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                            "justifyContent": "space-between",
                                            "paddingRight": "20px",
                                        },
                                    ),
                                    dcc.Store(id="filter-store", data=default_filters),
                                    dcc.Store(id="active-selection", data=None),
                                    # Start CLOSED; also track if we've ever opened before
                                    dcc.Store(
                                        id="sidebar-visibility-store",
                                        data={"visible": False, "opened_once": False},
                                    ),
                                    dcc.Store(id="selected-graphs", data=[]),
                                    dcc.Store(id="selected-data", data={}),
                                    # Tab 3 dedicated filter store
                                    dcc.Store(
                                        id="tab3-filter-store",
                                        data={
                                            "outlet_categories": [],
                                            "sales_center_codes": [],
                                            "shortfall_side": None,  # Quality shortfall / Performance shortfall / Both shortfalls
                                            "kpi_focus": None,  # Selected KPI name from Focus KPI cards
                                        },
                                    ),
                                    # ---- Filter bar ----
                                    html.Div(
                                        [
                                            # Row 1: Core categorical slicers (search + sliders removed)
                                            html.Div(
                                                dcc.Dropdown(
                                                    id="outlet-category-filter",
                                                    placeholder="Select Category (A/B/C/D)",
                                                    options=[
                                                        {"label": cat, "value": cat}
                                                        for cat in all_outlet_categories
                                                    ],
                                                    multi=True,
                                                ),
                                                style={"flex": "1", "margin": "0 10px"},
                                            ),
                                            html.Div(
                                                dcc.Dropdown(
                                                    id="region-filter",
                                                    placeholder="Select Region(s)",
                                                    options=[
                                                        {"label": reg, "value": reg}
                                                        for reg in all_regions
                                                    ],
                                                    multi=True,
                                                ),
                                                style={"flex": "1", "margin": "0 10px"},
                                            ),
                                            html.Div(
                                                dcc.Dropdown(
                                                    id="outlet-type-filter",
                                                    placeholder="Outlet Type",
                                                    options=[
                                                        {"label": t, "value": t}
                                                        for t in all_outlet_types
                                                    ],
                                                    multi=True,
                                                ),
                                                style={"flex": "1", "margin": "0 10px"},
                                            ),
                                            html.Button(
                                                "Reset All Filters",
                                                id="reset-button",
                                                n_clicks=0,
                                                style={
                                                    "height": "36px",
                                                    "marginLeft": "10px",
                                                },
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                            "padding": "6px 20px",
                                            "backgroundColor": "#f0f0f0",
                                        },
                                    ),
                                    # Row 3 removed per request (KPI Group, Specific KPI, Score Band, Units Band)
                                    # --------- Tabs ---------
                                    dcc.Tabs(
                                        id="tabs",
                                        value="tab1",
                                        children=[
                                            # ===== TAB 1: Dashboard =====
                                            dcc.Tab(
                                                label="Performance & Quality by Region",
                                                value="tab1",
                                                children=[tab1_layout()],
                                            ),
                                            # ===== TAB 2: Deep-dive (graphs) =====
                                            dcc.Tab(
                                                label="Parameter Correlation",
                                                value="tab2",
                                                children=[tab2_layout()],
                                            ),
                                            # ===== TAB 3: 5-Chart Dashboard =====
                                            dcc.Tab(
                                                label="Category & Type Diagnostics",
                                                value="tab3",
                                                children=[tab3_layout()],
                                            ),
                                        ],
                                        style={"marginTop": "10px"},
                                    ),
                                ],
                                style={"padding": "20px"},
                            ),
                        ],
                        style={"height": "100vh", "overflowY": "auto"},
                    ),
                    PanelResizeHandle(
                        id="sidebar-resize-handle",
                        children=html.Div(
                            style={
                                "backgroundColor": "#ccc",
                                "width": "5px",
                                "cursor": "col-resize",
                            }
                        ),
                        style={"display": "none"},
                    ),
                    Panel(
                        id="sidebar-panel",
                        children=[
                            html.Div(
                                id="sidebar",
                                children=[
                                    html.H2(
                                        "Controls",
                                        style={
                                            "margin": "8px 0 4px 0",
                                            "lineHeight": "1.1",
                                            "fontWeight": 800,
                                        },
                                    ),
                                    html.P(
                                        "Select charts to generate insights",
                                        style={
                                            "margin": "0",
                                            "color": "#6b7280",
                                            "fontSize": "13px",
                                        },
                                    ),
                                    # Selected chips / placeholder
                                    html.Div(
                                        id="selected-info",
                                        children=[
                                            html.Div(
                                                "No charts selected yet.",
                                                style={
                                                    "color": "#6b7280",
                                                    "fontSize": "13px",
                                                },
                                            )
                                        ],
                                        style={"margin": "4px 0 0 0"},
                                    ),
                                    html.Button(
                                        "Clear Selection",
                                        id="clear-selection",
                                        n_clicks=0,
                                        style={
                                            "width": "100%",
                                            "padding": "10px",
                                            "marginTop": "6px",
                                            "backgroundColor": "#e5e7eb",
                                            "color": "#111827",
                                            "border": "1px solid #d1d5db",
                                            "borderRadius": "8px",
                                            "cursor": "pointer",
                                        },
                                    ),
                                    # LLM data scope removed; always use full data for analysis
                                    # Insight mode selector
                                    html.Div(
                                        [
                                            html.Label(
                                                "Analysis Mode",
                                                style={
                                                    "fontWeight": "bold",
                                                    "fontSize": "14px",
                                                    "marginTop": "15px",
                                                },
                                            ),
                                            dcc.RadioItems(
                                                id="insight-mode-radio",
                                                options=[
                                                    {
                                                        "label": "Individual Insights",
                                                        "value": "individual",
                                                    },
                                                    {
                                                        "label": "Combined Insights",
                                                        "value": "combined",
                                                    },
                                                ],
                                                value="individual",
                                                labelStyle={
                                                    "display": "block",
                                                    "marginTop": "5px",
                                                },
                                            ),
                                        ],
                                        style={"marginTop": "10px"},
                                    ),
                                    # Model provider selector
                                    html.Div(
                                        [
                                            html.Label(
                                                "Model Provider",
                                                style={
                                                    "fontWeight": "bold",
                                                    "fontSize": "14px",
                                                    "marginTop": "12px",
                                                },
                                            ),
                                            dcc.RadioItems(
                                                id="model-provider",
                                                options=[
                                                    {
                                                        "label": "Gemini (default)",
                                                        "value": "gemini",
                                                    },
                                                    {
                                                        "label": "OpenRouter: DeepSeek R1",
                                                        "value": "openrouter",
                                                    },
                                                ],
                                                value="gemini",
                                                labelStyle={
                                                    "display": "block",
                                                    "marginTop": "5px",
                                                },
                                            ),
                                        ],
                                        style={"marginTop": "4px"},
                                    ),
                                    html.Button(
                                        "Generate Insights",
                                        id="generate-button",
                                        n_clicks=0,
                                        style={
                                            "width": "100%",
                                            "padding": "12px",
                                            "marginTop": "10px",
                                            "backgroundColor": "#007bff",
                                            "color": "white",
                                            "border": "none",
                                            "borderRadius": "8px",
                                            "cursor": "pointer",
                                        },
                                    ),
                                    dcc.Loading(
                                        id="generate-loading",
                                        type="default",
                                        fullscreen=False,
                                        color="#007bff",
                                        children=html.Div(id="generate-output"),
                                    ),
                                    html.Hr(style={"margin": "10px 0"}),
                                    html.Div(
                                        [
                                            html.Div(
                                                "LLM Payload Preview",
                                                style={
                                                    "fontWeight": 700,
                                                    "fontSize": "13px",
                                                },
                                            ),
                                            html.Div(
                                                id="llm-debug",
                                                style={
                                                    "fontSize": "12px",
                                                    "color": "#374151",
                                                },
                                            ),
                                        ]
                                    ),
                                ],
                                style={
                                    "padding": "16px 20px 40px",
                                    "backgroundColor": "#f8f9fa",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "gap": "6px",
                                    "height": "100%",
                                    "minHeight": 0,
                                    "overflowY": "auto",
                                    "overflowX": "hidden",
                                    "WebkitOverflowScrolling": "touch",
                                    "overscrollBehavior": "contain",
                                    "boxSizing": "border-box",
                                },
                            )
                        ],
                        style={
                            "minWidth": 0,
                            "width": 0,
                            "display": "none",
                            "height": "100vh",
                            "backgroundColor": "#f8f9fa",
                        },
                    ),
                ],
            )
        ],
        style={"height": "100vh", "fontFamily": '"Roboto", sans-serif'},
    )

    # ----- Toggle sidebar visibility -----
    @app.callback(
        Output("sidebar-panel", "style"),
        Output("sidebar-resize-handle", "style"),
        Output("sidebar-visibility-store", "data"),
        Input("sidebar-toggle-button", "n_clicks"),
        State("sidebar-visibility-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_sidebar_visibility(n_clicks, visibility_data):
        if not n_clicks:
            raise PreventUpdate

        is_visible = bool(visibility_data.get("visible", False))
        opened_once = bool(visibility_data.get("opened_once", False))
        new_visibility = not is_visible

        if new_visibility:
            # OPENING
            if not opened_once:
                # First open at 25% of the screen width
                panel_style = {
                    "height": "100vh",
                    "backgroundColor": "#f8f9fa",
                    "width": "25%",
                }
                new_store = {"visible": True, "opened_once": True}
            else:
                panel_style = {"height": "100vh", "backgroundColor": "#f8f9fa"}
                new_store = {"visible": True, "opened_once": True}
            handle_style = {
                "width": "5px",
                "cursor": "col-resize",
                "backgroundColor": "#ccc",
            }
            return panel_style, handle_style, new_store
        else:
            # CLOSING
            panel_style = {
                "minWidth": 0,
                "width": 0,
                "display": "none",
                "height": "100vh",
                "backgroundColor": "#f8f9fa",
            }
            handle_style = {"display": "none"}
            new_store = {"visible": False, "opened_once": opened_once}
            return panel_style, handle_style, new_store

    # ----- Generate report (multi-chart) -----
    @app.callback(
        Output("insight-mode-radio", "options"),
        Output("insight-mode-radio", "value"),
        Input("selected-graphs", "data"),
    )
    def guard_insight_mode(selected_graphs):
        sel = list(selected_graphs or [])
        base_opts = [
            {"label": "Individual Insights", "value": "individual"},
            {"label": "Combined Insights", "value": "combined"},
        ]
        if len(sel) <= 1:
            return ([base_opts[0]], "individual")
        return (base_opts, "combined")

    @app.callback(
        Output("generate-output", "children"),
        Output("llm-debug", "children"),
        Input("generate-button", "n_clicks"),
        State("selected-graphs", "data"),
        State("selected-data", "data"),
        State("filter-store", "data"),
        State("insight-mode-radio", "value"),
        State("model-provider", "value"),
        # Include latest Tab 2 axis/legend selections so prompts always reflect current UI state
        State("t2-x-param", "value"),
        State("t2-y-param", "value"),
        State("t2-color-dim", "value"),
        prevent_initial_call=True,
    )
    def generate_report(
        n_clicks,
        selected_graphs,
        selected_data,
        filters,
        insight_mode,
        model_provider,
        t2_x_current,
        t2_y_current,
        t2_color_current,
    ):
        # Trigger visible loading state
        if not n_clicks:
            return "", no_update
        if not selected_graphs:
            return html.Div(
                [
                    html.H4("No charts selected.", style={"color": "#991B1B"}),
                    html.P("Use “Select this graph” under one or more charts."),
                ]
            ), no_update

        def label(gid):
            return GRAPH_LABELS.get(gid, gid)

        # Prefer full snapshot for LLM; fall back to chart-scoped data
        def pick_meta_for(gid: str, meta_obj: dict | None):
            if not isinstance(meta_obj, dict):
                return None
            # If already in flat format
            if "columns" in meta_obj and "records" in meta_obj:
                return meta_obj
            # For q3, prefer 'chart' (drilldown state) so LLM reflects the current view
            if gid == "q3" and isinstance(meta_obj.get("chart"), dict):
                return meta_obj["chart"]
            # Default: prefer full snapshot for stability
            if isinstance(meta_obj.get("full"), dict):
                return meta_obj["full"]
            if isinstance(meta_obj.get("chart"), dict):
                return meta_obj["chart"]
            return None

        charts_payload = []
        for gid in selected_graphs:
            meta_all = (selected_data or {}).get(gid)
            meta = pick_meta_for(gid, meta_all)
            if not meta:
                continue
            item = {
                "graph_id": gid,
                "graph_label": label(gid),
                "filters": filters,
                "columns": meta.get("columns", []),
                "n_rows": meta.get("n_rows", 0),
                "rows": meta.get("records", []),
            }
            # Attach generic chart-level metadata if provided by the selector step
            try:
                if isinstance(meta_all, dict) and isinstance(
                    meta_all.get("meta"), dict
                ):
                    item["meta"] = meta_all["meta"]
            except Exception:
                pass
            # Enrich Tab 3 first chart with both datasets when available
            if gid == "t3-graph-1" and isinstance(meta_all, dict):
                alt_full = meta_all.get("alt_full")
                alt_chart = meta_all.get("alt_chart")
                if isinstance(alt_full, dict):
                    item["alt_full"] = alt_full
                if isinstance(alt_chart, dict):
                    item["alt_chart"] = alt_chart
                # Do not add the secondary (raw outlet) table as a separate chart entry.
                # It remains attached as alt_full/alt_chart on the main item if needed for internal use.
                # Also add the derived KPI gap table that powers the diverging bar
                gap_meta = meta_all.get("gap_chart") or meta_all.get("gap_full")
                if isinstance(gap_meta, dict):
                    charts_payload.append(
                        {
                            "graph_id": f"{gid}-gaps",
                            "graph_label": label(gid) + " — KPI gaps",
                            "filters": filters,
                            "columns": gap_meta.get("columns", []),
                            "n_rows": gap_meta.get("n_rows", 0),
                            "rows": gap_meta.get("records", []),
                        }
                    )
            # Ensure q3 reflects current drilldown (override from live filters)
            if gid == "q3":
                try:
                    _q1, _q2, _q3, _q4, _q5 = t1_get_filtered_frames(
                        tab1, (filters or {})
                    )
                    regs_sel = list((filters or {}).get("regions") or [])
                    live_df = _q4 if len(regs_sel) == 1 else _q1
                    if isinstance(live_df, pd.DataFrame) and not live_df.empty:
                        item["columns"] = [str(c) for c in live_df.columns]
                        item["rows"] = live_df.to_dict("records")
                        item["n_rows"] = len(item["rows"])
                except Exception:
                    pass
            # Enrich/override Tab 2 dynamic chart metadata with the CURRENT UI selections
            if gid == "t2-graph-dyn" and isinstance(meta_all, dict):
                # Start from any stored meta then override x/y/color with live values
                try:
                    live_meta = dict(meta_all.get("meta") or {})
                except Exception:
                    live_meta = {}
                if t2_x_current:
                    live_meta["x"] = t2_x_current
                if t2_y_current:
                    live_meta["y"] = t2_y_current
                if t2_color_current:
                    live_meta["color"] = t2_color_current
                if live_meta:
                    item["meta"] = live_meta
            charts_payload.append(item)

        if not charts_payload:
            return html.Div(
                [
                    html.H4("No data available.", style={"color": "#991B1B"}),
                    html.P("Re-select charts after adjusting filters."),
                ]
            ), no_update

        # Derive top-level metadata for prompt (x/y/legend) when available
        top_metadata = {}
        try:
            for ch in charts_payload:
                m = ch.get("meta") if isinstance(ch, dict) else None
                if isinstance(m, dict) and ("x" in m and "y" in m):
                    top_metadata = {
                        "x_axis": m.get("x", ""),
                        "y_axis": m.get("y", ""),
                        "legend": m.get("color") or m.get("legend") or "",
                    }
                    break
        except Exception:
            top_metadata = {}

        payload = {"charts": charts_payload, "metadata": top_metadata}
        print(payload)

        # Build sidebar debug preview for all selected charts, including q2
        def preview_all(charts):
            sections = []
            for ch in charts:
                cols = ch.get("columns", [])
                rows = ch.get("rows", [])
                n = ch.get("n_rows", len(rows))
                title = ch.get("graph_label", ch.get("graph_id"))
                header = html.Div(
                    [
                        html.Div(str(title), style={"fontWeight": 600}),
                        html.Div(f"Rows: {n}", style={"color": "#6b7280"}),
                    ],
                    style={"margin": "6px 0 4px"},
                )
                if not cols or not rows:
                    sections.append(
                        html.Div(
                            [
                                header,
                                html.Div(
                                    "No data (empty payload).",
                                    style={"color": "#991B1B", "fontSize": "12px"},
                                ),
                            ]
                        )
                    )
                    continue
                sample = rows[:8]
                table = dash_table.DataTable(
                    columns=[{"name": str(c), "id": str(c)} for c in cols],
                    data=sample,
                    page_size=8,
                    style_table={
                        "overflowX": "auto",
                        "border": "1px solid #e5e7eb",
                        "borderRadius": "6px",
                    },
                    style_cell={"fontSize": 11, "padding": "6px", "textAlign": "left"},
                )
                sections.append(html.Div([header, table]))
            if not sections:
                return html.Div(
                    "No selected charts to preview.", style={"color": "#6b7280"}
                )
            return html.Div(sections)

        debug_view = preview_all(charts_payload)
        # Add brief preamble to steer models when axis metadata exists
        focus_hint = ""
        try:
            for ch in charts_payload:
                if ch.get("graph_id") == "t2-graph-dyn" and isinstance(
                    ch.get("meta"), dict
                ):
                    mx = ch["meta"]
                    focus_hint = (
                        f"Focus your analysis of the parameter relationship on the selected axes: "
                        f"x={mx.get('x')}, y={mx.get('y')}, color/legend={mx.get('color')}.\n"
                    )
                    break
        except Exception:
            pass

        # Context/theme and domain knowledge base for CR KPI DW
        context_text = os.environ.get("INSIGHTS_CONTEXT", "").strip()
        # Resolve provider early so we can use it in multi-chart individual generation
        provider = (
            (model_provider or os.environ.get("INSIGHTS_PROVIDER", "gemini"))
            .strip()
            .lower()
        )

        # If multiple charts are selected and mode is individual, generate one insight per chart
        if (insight_mode or "individual") == "individual" and len(charts_payload) > 1:
            sections = []
            for ch in charts_payload:
                ch_meta = ch.get("meta") if isinstance(ch, dict) else None
                # Build per-chart focus hint
                fh = ""
                if isinstance(ch_meta, dict):
                    xh = ch_meta.get("x")
                    yh = ch_meta.get("y")
                    lh = ch_meta.get("color") or ch_meta.get("legend")
                    if xh or yh or lh:
                        fh = f"Focus your analysis on the selected axes: x={xh}, y={yh}, color/legend={lh}.\n"
                # Per-chart column focus metadata for prompt
                per_meta = {}
                if isinstance(ch_meta, dict) and ("x" in ch_meta and "y" in ch_meta):
                    per_meta = {
                        "x_axis": ch_meta.get("x", ""),
                        "y_axis": ch_meta.get("y", ""),
                        "legend": ch_meta.get("color") or ch_meta.get("legend") or "",
                    }
                per_payload = {"charts": [ch], "metadata": per_meta}
                per_prompt = build_prompt_individual(per_payload, context_text, fh)

                # Log per-chart prompt
                try:
                    from datetime import datetime

                    os.makedirs("logs", exist_ok=True)
                    meta = {
                        "ts": datetime.utcnow().isoformat() + "Z",
                        "mode": "individual-multi",
                        "provider": provider,
                        "model": MODEL_NAME,
                        "selected_graphs": [ch.get("graph_id")],
                        "graph_label": ch.get("graph_label"),
                        "focus_hint": fh.strip(),
                    }
                    entry = {
                        "meta": meta,
                        "metadata": per_meta,
                        "charts_meta": (
                            [{"graph_id": ch.get("graph_id"), "meta": ch_meta}]
                            if isinstance(ch_meta, dict)
                            else []
                        ),
                        "prompt": per_prompt,
                        "prompt_lines": per_prompt.splitlines(),
                    }
                    with open("logs/insights_prompts.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps(entry, ensure_ascii=False, indent=2) + "\n")
                except Exception:
                    pass

                # Call LLM for this chart
                if provider == "openrouter":
                    per_text, per_err = generate_markdown_openrouter(per_prompt)
                else:
                    per_text, per_err = generate_markdown_from_prompt(
                        per_prompt, model_name=MODEL_NAME, api_key=GOOGLE_API_KEY
                    )
                if per_err:
                    sections.append(
                        html.Div(
                            [
                                html.H5(
                                    f"Error generating insight for {ch.get('graph_label')}",
                                    style={"color": "#991B1B"},
                                ),
                                html.P(str(per_err)),
                            ]
                        )
                    )
                    continue

                # Unwrap and format per-chart output
                def _unwrap_code_fence_local(s: str | None) -> str:
                    if not s:
                        return ""
                    text = s.strip()
                    m = re.match(
                        r"^```(?:[a-zA-Z0-9_-]+)?\s*\n(.*)\n```$", text, flags=re.S
                    )
                    if m:
                        return m.group(1).strip()
                    if text.startswith("```") and text.count("```") >= 2:
                        first_close = text.find("```", 3)
                        if first_close != -1:
                            inner = text[3:first_close]
                            rest = text[first_close + 3 :].strip()
                            if not rest:
                                return inner.strip()
                    return text

                cleaned_local = _unwrap_code_fence_local(per_text)

                def _to_point_form_local(md: str) -> str:
                    try:
                        s = (md or "").strip()
                        if not s:
                            return s
                        if (
                            "\n- " in s
                            or s.lstrip().startswith("- ")
                            or "\n* " in s
                            or s.lstrip().startswith("* ")
                        ):
                            lines = s.split("\n")
                            out_lines = []
                            for line in lines:
                                if (
                                    line.lstrip().startswith(("- ", "* "))
                                    and len(line) > 160
                                ):
                                    import re as _re

                                    text = line.lstrip()[2:].strip()
                                    sentences = [
                                        t.strip()
                                        for t in _re.split(r"(?<=[.!?])\s+", text)
                                        if t.strip()
                                    ]
                                    if sentences:
                                        out_lines.append(line)
                                        for sent in sentences[1:]:
                                            out_lines.append(f"  - {sent}")
                                        continue
                                out_lines.append(line)
                            return "\n".join(out_lines)
                        blocks = [b.strip() for b in s.split("\n\n") if b.strip()]
                        out = []
                        for b in blocks:
                            if b.startswith(("#", "##", "###")):
                                out.append(b)
                            else:
                                import re as _re

                                sentences = [
                                    t.strip()
                                    for t in _re.split(r"(?<=[.!?])\s+", b)
                                    if t.strip()
                                ]
                                if not sentences:
                                    out.append(f"- {b}")
                                else:
                                    out.append(f"- {sentences[0]}")
                                    for sent in sentences[1:]:
                                        out.append(f"  - {sent}")
                        return "\n\n".join(out)
                    except Exception:
                        return md

                pointy_local = _to_point_form_local(cleaned_local)
                sections.append(
                    html.Div(
                        [
                            html.H4(
                                ch.get("graph_label") or ch.get("graph_id"),
                                style={"color": "#007bff"},
                            ),
                            dcc.Markdown(
                                pointy_local or "_No content returned._",
                                link_target="_blank",
                            ),
                        ],
                        style={"marginBottom": "24px"},
                    )
                )

            return html.Div(sections), debug_view
        # Use the same output structure for combined and individual insights
        # by routing both modes through the individual prompt builder.
        prompt = build_prompt_individual(payload, context_text, focus_hint)

        # Log prompt with metadata for insights (provider, model, selected graphs)
        try:
            from datetime import datetime

            os.makedirs("logs", exist_ok=True)
            meta = {
                "ts": datetime.utcnow().isoformat() + "Z",
                "mode": insight_mode,
                "provider": (
                    model_provider or os.environ.get("INSIGHTS_PROVIDER", "gemini")
                )
                .strip()
                .lower(),
                "model": MODEL_NAME,
                "selected_graphs": list(selected_graphs or []),
                "focus_hint": focus_hint.strip(),
            }
            charts_meta = []
            try:
                for ch in charts_payload:
                    if isinstance(ch.get("meta"), dict):
                        charts_meta.append(
                            {"graph_id": ch.get("graph_id"), "meta": ch.get("meta")}
                        )
            except Exception:
                pass
            # Improve readability: include prompt_lines (array of lines) alongside raw prompt
            try:
                prompt_lines = (prompt or "").splitlines()
            except Exception:
                prompt_lines = []
            entry = {
                "meta": meta,
                "metadata": top_metadata,
                "charts_meta": charts_meta,
                "prompt": prompt,
                "prompt_lines": prompt_lines,
            }
            with open("logs/insights_prompts.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, indent=2) + "\n")
        except Exception:
            pass

        # Provider can be chosen in UI; fallback to env if UI missing
        provider = (
            (model_provider or os.environ.get("INSIGHTS_PROVIDER", "gemini"))
            .strip()
            .lower()
        )
        # Print/emit concise metadata for debugging prompt context
        try:
            _metas = []
            for ch in charts_payload:
                if isinstance(ch.get("meta"), dict):
                    _metas.append(
                        {"graph_id": ch.get("graph_id"), "meta": ch.get("meta")}
                    )
            print(
                {
                    "insights_meta": {
                        "mode": insight_mode,
                        "provider": provider,
                        "model": MODEL_NAME,
                        "selected_graphs": [c.get("graph_id") for c in charts_payload],
                        "charts_meta": _metas,
                        "metadata": top_metadata,
                    }
                }
            )
        except Exception:
            pass
        if provider == "openrouter":
            llm_text, err = generate_markdown_openrouter(prompt)
        else:
            llm_text, err = generate_markdown_from_prompt(
                prompt, model_name=MODEL_NAME, api_key=GOOGLE_API_KEY
            )
        if err:
            return html.Div(
                [
                    html.H4("Error Generating Report", style={"color": "#991B1B"}),
                    html.P(f"LLM error: {err}"),
                ]
            ), debug_view

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
                    rest = text[first_close + 3 :].strip()
                    if not rest:
                        return inner.strip()
            return text

        cleaned = _unwrap_code_fence(llm_text)

        # Prefer bullet/point form for readability: if the response is not already in bullets,
        # lightly transform paragraphs into bullets without altering content. This is a best-effort
        # display-only formatting; it does not change the underlying response text.
        def _to_point_form(md: str) -> str:
            try:
                s = (md or "").strip()
                if not s:
                    return s
                # If it already contains bullets, keep as-is
                if (
                    "\n- " in s
                    or s.lstrip().startswith("- ")
                    or "\n* " in s
                    or s.lstrip().startswith("* ")
                ):
                    # Also try to break long lines inside each existing bullet into sub-bullets by sentences
                    lines = s.split("\n")
                    out_lines = []
                    for line in lines:
                        if line.lstrip().startswith(("- ", "* ")) and len(line) > 160:
                            # Split into sentences and indent as sub-bullets
                            import re as _re

                            text = line.lstrip()[2:].strip()
                            sentences = [
                                t.strip()
                                for t in _re.split(r"(?<=[.!?])\s+", text)
                                if t.strip()
                            ]
                            if sentences:
                                # First sentence remains the main bullet
                                out_lines.append(line)
                                # Subsequent sentences become indented sub-bullets
                                for sent in sentences[1:]:
                                    out_lines.append(f"  - {sent}")
                                continue
                        out_lines.append(line)
                    return "\n".join(out_lines)
                # Split by double newlines into blocks and prefix with '- ' when appropriate
                blocks = [b.strip() for b in s.split("\n\n") if b.strip()]
                # Keep headings intact; bullet non-heading blocks
                out = []
                for b in blocks:
                    if b.startswith(("#", "##", "###")):
                        out.append(b)
                    else:
                        # Convert a paragraph into a parent bullet and sub-bullets by sentences
                        import re as _re

                        sentences = [
                            t.strip()
                            for t in _re.split(r"(?<=[.!?])\s+", b)
                            if t.strip()
                        ]
                        if not sentences:
                            out.append(f"- {b}")
                        else:
                            out.append(f"- {sentences[0]}")
                            for sent in sentences[1:]:
                                out.append(f"  - {sent}")
                return "\n\n".join(out)
            except Exception:
                return md

        pointy = _to_point_form(cleaned)
        return html.Div(
            [
                html.H4("Generated Insights", style={"color": "#007bff"}),
                dcc.Markdown(pointy or "_No content returned._", link_target="_blank"),
            ]
        ), debug_view

    # ----- Filter controller: click-to-filter + global slicers -----
    @app.callback(
        Output("filter-store", "data"),
        Output("active-selection", "data"),
        Output("outlet-category-filter", "value"),
        Output("region-filter", "value"),
        Output("outlet-type-filter", "value"),
        Input("reset-button", "n_clicks"),
        Input("outlet-category-filter", "value"),
        Input("region-filter", "value"),
        Input("outlet-type-filter", "value"),
        # Input('graph-q1', 'clickData'),
        Input("graph-q2", "clickData"),
        Input("graph-q3", "clickData"),
        Input("graph-q4", "clickData"),
        Input("graph-q5", "clickData"),
        Input("graph-q6", "clickData"),
        Input("t2-graph-dynamic", "clickData"),
        # Tab 3 clicks should also update global filters where applicable
        Input("t3-graph-1", "clickData"),
        Input("t3-graph-2", "clickData"),
        # Input('t3-graph-5', 'clickData'),
        State("filter-store", "data"),
        State("active-selection", "data"),
        State("t2-color-dim", "value"),
        prevent_initial_call=True,
    )
    def update_filters_and_ui(
        reset_clicks,
        outlet_cats,
        regions,
        outlet_types,
        click_q2,
        click_q3,
        click_q4,
        click_q5,
        click_q6,
        click_t2_dyn,
        click_t3_g1,
        click_t3_g2,
        current_filters,
        active_selection,
        t2_color_dim,
    ):
        def make_key(graph_id, point):
            def _cd(p, i=0, default=None):
                try:
                    return p.get("customdata", [default])[i]
                except Exception:
                    return default

            # graph-q1 removed
            if graph_id == "graph-q2":
                # stacked 100% bar: customdata carries [region, category]
                reg = _cd(point, 0)
                cat = _cd(point, 1)
                return f"q2|category={cat}|region={reg}"
            if graph_id == "graph-q3":
                # region-level scatter: customdata carries [region]
                reg = _cd(point, 0)
                return f"q3|region={reg}"
            if graph_id == "graph-q4":
                return f"q4|region={_cd(point, 0)}|outlet={_cd(point, 1)}"
            if graph_id == "graph-q5":
                return f"q5|region={_cd(point, 0)}|outlet={_cd(point, 1)}"
            if graph_id == "graph-q6":
                # category count bar: x is outlet_category
                return f"q6|category={point.get('x')}"
            return None

        # removed unused Tab 2 key builder

        trig = ctx.triggered[0]
        trig_id = trig["prop_id"].split(".")[0]

        if trig_id == "reset-button":
            df = default_filters
            return (df, None, [], [], [])

        if trig_id in ("outlet-category-filter", "region-filter", "outlet-type-filter"):
            new_filters = current_filters.copy()
            new_filters["outlet_categories"] = outlet_cats or []
            new_filters["regions"] = regions or []
            new_filters["outlet_types"] = outlet_types or []
            return (
                new_filters,
                None,
                new_filters["outlet_categories"],
                new_filters["regions"],
                new_filters["outlet_types"],
            )

        if trig_id == "t2-graph-dynamic" and trig.get("value"):
            # Update global filters based on clicked Tab 2 point, with toggle behavior
            try:
                point = trig["value"]["points"][0]
            except Exception:
                point = {}
            cd = point.get("customdata") or []
            # customdata order: [outlet_name/sales_outlet, rgn, outlet_category, outlet_type]
            reg = cd[1] if len(cd) >= 2 else None
            cat = cd[2] if len(cd) >= 3 else None
            otype = cd[3] if len(cd) >= 4 else None
            # Build a stable key for toggle
            key_parts = [f"r={reg}" if reg else None]
            if (t2_color_dim or "") == "outlet_category" and cat:
                key_parts.append(f"cat={cat}")
            if (t2_color_dim or "") == "outlet_type" and otype:
                key_parts.append(f"type={otype}")
            key = (
                "t2|" + "|".join([p for p in key_parts if p])
                if any(key_parts)
                else None
            )

            # Toggle: clicking the same selection clears only the affected filters
            if active_selection == key and key is not None:
                nf = dict(current_filters or {})
                # Clear region/category/type filters we may have set
                if reg:
                    nf["regions"] = []
                if cat:
                    nf["outlet_categories"] = []
                if otype:
                    nf["outlet_types"] = []
                # Also set a toast message for Tab 2
                # We piggyback by setting a side-effect store via a separate callback below
                return (
                    nf,
                    None,
                    nf.get("outlet_categories", []),
                    nf.get("regions", []),
                    nf.get("outlet_types", []),
                )

            # Otherwise, apply filters and store active key
            nf = dict(current_filters or {})
            if reg:
                nf["regions"] = [reg]
            if (t2_color_dim or "") == "outlet_category" and cat:
                nf["outlet_categories"] = [cat]
            if (t2_color_dim or "") == "outlet_type" and otype:
                nf["outlet_types"] = [otype]
            # Apply and set active key
            return (
                nf,
                key,
                nf.get("outlet_categories", []),
                nf.get("regions", []),
                nf.get("outlet_types", []),
            )

        # Tab 3 -> Global filters: diverging bar click toggles outlet_category in global filters
        if trig_id == "t3-graph-1" and trig.get("value"):
            point = trig["value"]["points"][0]
            try:
                cat = (point.get("customdata") or [None])[0]
            except Exception:
                cat = None
            if not cat:
                return (
                    current_filters,
                    active_selection,
                    current_filters.get("outlet_categories", []),
                    current_filters.get("regions", []),
                    current_filters.get("outlet_types", []),
                )
            key = f"t3g1|category={cat}"
            # Toggle behavior: clicking same category clears only the category filter
            if active_selection == key:
                nf = dict(current_filters or {})
                nf["outlet_categories"] = []
                return (
                    nf,
                    None,
                    nf.get("outlet_categories", []),
                    nf.get("regions", []),
                    nf.get("outlet_types", []),
                )
            # Set selected category in global filters
            nf = dict(current_filters or {})
            nf["outlet_categories"] = [cat]
            return (
                nf,
                key,
                nf.get("outlet_categories", []),
                nf.get("regions", []),
                nf.get("outlet_types", []),
            )

        if trig_id.startswith("graph-") and trig.get("value"):
            point = trig["value"]["points"][0]
            key = make_key(trig_id, point)

            if active_selection == key:
                df = default_filters
                return (df, None, [], [], [])

            new_filters = default_filters.copy()
            if trig_id == "graph-q1":
                if point.get("y"):
                    new_filters["regions"] = [point.get("y")]
            elif trig_id == "graph-q2":
                # stacked bar: customdata [region, category]
                try:
                    reg = point.get("customdata", [None, None])[0]
                    cat = point.get("customdata", [None, None])[1]
                except Exception:
                    reg, cat = None, None
                if reg:
                    new_filters["regions"] = [reg]
                if cat:
                    new_filters["outlet_categories"] = [cat]
            elif trig_id == "graph-q3":
                # region-level scatter: customdata [region]
                try:
                    reg = point.get("customdata", [None])[0]
                except Exception:
                    reg = None
                if reg:
                    new_filters["regions"] = [reg]
            elif trig_id in ("graph-q4", "graph-q5"):
                # barh: y=Outlet
                if point.get("y"):
                    new_filters["outlets"] = [point.get("y")]
            elif trig_id == "graph-q6":
                # bar: x=outlet_category
                if point.get("x"):
                    new_filters["outlet_categories"] = [point.get("x")]

            return (
                new_filters,
                key,
                new_filters.get("outlet_categories", []),
                new_filters.get("regions", []),
                new_filters.get("outlet_types", []),
            )

        return (
            current_filters,
            active_selection,
            current_filters.get("outlet_categories", []),
            current_filters.get("regions", []),
            current_filters.get("outlet_types", []),
        )

    # ----- Plot updates (stable colors via color_discrete_map) -----
    @app.callback(
        Output("graph-q3", "figure"),
        Output("graph-q6", "figure"),
        Output("graph-q2", "figure"),
        Input("filter-store", "data"),
    )
    def update_graphs(filters):
        # Build filtered figures for q3 and q6
        figs_filtered = build_tab1_figures(
            tab1,
            filters,
            all_outlet_categories,
            all_regions,
            outlet_color_map,
            region_color_map,
            base_palette,
            GRAPH_LABELS,
        )
        # Build unfiltered figure for q2 (percentage chart should ignore filters)
        figs_unfiltered = build_tab1_figures(
            tab1,
            {},
            all_outlet_categories,
            all_regions,
            outlet_color_map,
            region_color_map,
            base_palette,
            GRAPH_LABELS,
        )
        # figs order: q1, q2, q3, q4, q5, q6
        return figs_filtered[2], figs_filtered[5], figs_unfiltered[1]

    # Tab 1 KPI cards removed per spec (no totals/overall at top)

    # ----- Tab 1 drilldown: show number of outlets in selected region -----
    @app.callback(Output("tab1-drilldown", "children"), Input("graph-q3", "clickData"))
    def tab1_region_drill(c3):
        # Drilldown now rendered on the same scatter; keep this hidden container empty
        return None

    # ----- Multi-select buttons: capture selections & store snapshots -----
    @app.callback(
        Output("selected-graphs", "data"),
        # Visual feedback on selected buttons
        Output("btn-select-q1", "aria-pressed"),
        Output("btn-select-q2", "aria-pressed"),
        Output("btn-select-q3", "aria-pressed"),
        Output("btn-select-q4", "aria-pressed"),
        Output("btn-select-q5", "aria-pressed"),
        Output("btn-select-q6", "aria-pressed"),
        Output("btn-select-t2-dyn", "aria-pressed"),
        Output("btn-select-t3-1", "aria-pressed"),
        Output("btn-select-t3-3", "aria-pressed"),
        Output("selected-data", "data"),
        Output("selected-info", "children"),
        # Tab 1 buttons
        Input("btn-select-q1", "n_clicks"),
        Input("btn-select-q2", "n_clicks"),
        Input("btn-select-q3", "n_clicks"),
        Input("btn-select-q4", "n_clicks"),
        Input("btn-select-q5", "n_clicks"),
        Input("btn-select-q6", "n_clicks"),
        # Tab 2 button
        Input("btn-select-t2-dyn", "n_clicks"),
        # Tab 3 buttons
        Input("btn-select-t3-1", "n_clicks"),
        Input("btn-select-t3-3", "n_clicks"),
        # Clear selection button in sidebar
        Input("clear-selection", "n_clicks"),
        # States
        State("filter-store", "data"),
        State("tab3-filter-store", "data"),
        State("selected-graphs", "data"),
        State("selected-data", "data"),
        # Tab 2 control states for LLM metadata
        State("t2-x-param", "value"),
        State("t2-y-param", "value"),
        State("t2-color-dim", "value"),
        prevent_initial_call=True,
    )
    def handle_select(*args):
        (
            btn1,
            btn2,
            btn3,
            btn4,
            btn5,
            btn6,
            t2dyn,
            t3b1,
            t3b3,
            clear_btn,
            filters,
            tab3_local,
            selected_graphs,
            selected_data,
            t2_x,
            t2_y,
            t2_color,
        ) = args
        triggered = ctx.triggered_id
        if triggered is None:
            raise PreventUpdate

        selected_graphs = list(selected_graphs or [])
        selected_data = dict(selected_data or {})

        # Clear selection request from sidebar
        if triggered == "clear-selection":
            info = html.Div(
                "No charts selected yet.",
                style={"color": "#6b7280", "fontSize": "13px"},
            )
            pressed = ["false"] * 9
            return [], *pressed, {}, info

        # Helper to add/remove
        def toggle(graph_id: str, df_full, df_chart):
            nonlocal selected_graphs, selected_data
            if graph_id in selected_graphs:
                selected_graphs = [g for g in selected_graphs if g != graph_id]
                selected_data.pop(graph_id, None)
            else:
                selected_graphs.append(graph_id)
                selected_data[graph_id] = {
                    "full": pack_df(df_full),
                    "chart": pack_df(df_chart),
                }

        def _basic_stats(dframe, cols):
            import pandas as _pd

            stats = {}
            if not isinstance(dframe, _pd.DataFrame) or dframe.empty:
                return stats
            for c in cols:
                if c in dframe.columns:
                    s = (
                        _pd.to_numeric(dframe[c], errors="coerce")
                        if not _pd.api.types.is_numeric_dtype(dframe[c])
                        else dframe[c]
                    )
                    try:
                        stats[c] = {
                            "min": float(_pd.to_numeric(s, errors="coerce").min()),
                            "max": float(_pd.to_numeric(s, errors="coerce").max()),
                            "mean": float(_pd.to_numeric(s, errors="coerce").mean()),
                            "nulls": int(s.isna().sum()),
                        }
                    except Exception:
                        pass
            stats["n"] = int(len(dframe))
            return stats

        # Tab 1 mapping (ensure datasets match what's drawn)
        if triggered.startswith("btn-select-q"):
            # Build both full (unfiltered) and chart (current-filtered) datasets
            df_q1_full, df_q2_full, df_q3_full, df_q4_full, df_q5_full = (
                t1_get_filtered_frames(tab1, {})
            )
            df_q1_chart, df_q2_chart, df_q3_chart, df_q4_chart, df_q5_chart = (
                t1_get_filtered_frames(tab1, (filters or {}))
            )
            # For q3, mirror the figure behavior: use region aggregates unless exactly one region selected
            regs_sel = list((filters or {}).get("regions") or [])
            q3_full_df = df_q1_full
            q3_chart_df = df_q4_chart if len(regs_sel) == 1 else df_q1_chart

            # q6 figure shows aggregated counts by category; reproduce here
            def _cat_counts(detail_df, fallback_df):
                import pandas as _pd

                d = (
                    detail_df
                    if isinstance(detail_df, _pd.DataFrame) and not detail_df.empty
                    else fallback_df
                )
                if not isinstance(d, _pd.DataFrame) or d.empty:
                    return _pd.DataFrame(columns=["category", "count"])
                cat_col = (
                    "outlet_category"
                    if "outlet_category" in d.columns
                    else ("Category" if "Category" in d.columns else None)
                )
                if not cat_col:
                    return _pd.DataFrame(columns=["category", "count"])
                try:
                    c = (
                        d[[cat_col]]
                        .dropna()
                        .groupby(cat_col, dropna=False)
                        .size()
                        .reset_index(name="count")
                    )
                    c = c.rename(columns={cat_col: "category"})
                    # order A-D when present
                    c["category"] = _pd.Categorical(
                        c["category"], categories=["A", "B", "C", "D"], ordered=True
                    )
                    c = c.sort_values("category")
                except Exception:
                    c = _pd.DataFrame(columns=["category", "count"])
                return c

            id_map = {
                "btn-select-q1": ("q1", df_q1_full, df_q1_chart),
                # q2 ignores filters in the figure; pass unfiltered for both full and chart
                "btn-select-q2": ("q2", df_q2_full, df_q2_full),
                "btn-select-q3": ("q3", q3_full_df, q3_chart_df),
                "btn-select-q4": ("q4", df_q4_full, df_q4_chart),
                "btn-select-q5": ("q5", df_q5_full, df_q5_chart),
                # q6 should receive aggregated counts to match the figure
                "btn-select-q6": (
                    "q6",
                    _cat_counts(df_q4_full, df_q1_full),
                    _cat_counts(df_q4_chart, df_q1_chart),
                ),
            }
            gid, df_full, df_chart = id_map[triggered]
            toggle(gid, df_full, df_chart)
            # Attach meta per figure where applicable
            if gid == "q3":
                # Performance vs Quality scatter by region/outlet
                try:
                    import pandas as _pd

                    d = (
                        df_chart
                        if isinstance(df_chart, _pd.DataFrame)
                        else _pd.DataFrame()
                    )
                    xcol, ycol = "avg_rate_quality", "avg_rate_performance"
                    if "rate_quality" in d.columns and "rate_performance" in d.columns:
                        xcol, ycol = "rate_quality", "rate_performance"
                    # Legend determination based on view
                    legend_col = (
                        "outlet_category"
                        if "outlet_category" in d.columns
                        else ("rgn" if "rgn" in d.columns else None)
                    )
                    # correlation
                    r = None
                    try:
                        x2 = _pd.to_numeric(d[xcol], errors="coerce")
                        y2 = _pd.to_numeric(d[ycol], errors="coerce")
                        r = float(x2.corr(y2)) if len(d) >= 2 else None
                    except Exception:
                        pass
                    md = selected_data.get(gid, {})
                    md["meta"] = {
                        "x": xcol,
                        "y": ycol,
                        "color": legend_col,
                        "stats": _basic_stats(d, [xcol, ycol]),
                        "correlation_r": r,
                    }
                    selected_data[gid] = md
                except Exception:
                    pass
        # Tab 2 dynamic (store UNFILTERED datasets for LLM)
        elif triggered == "btn-select-t2-dyn":
            ret_full = t2_get_filtered_frames(tab2, {})
            ret_chart = t2_get_filtered_frames(tab2, (filters or {}))
            df1_full = ret_full[0] if isinstance(ret_full, tuple) else ret_full
            df1_chart = ret_chart[0] if isinstance(ret_chart, tuple) else ret_chart
            toggle("t2-graph-dyn", df1_full, df1_chart)
            # Attach axis/color selections for LLM prompt only when selected
            if "t2-graph-dyn" in selected_graphs:
                md = selected_data.get("t2-graph-dyn", {})
                # compute r and stats from chart dataframe
                try:
                    import pandas as _pd

                    d = (
                        df1_chart
                        if isinstance(df1_chart, _pd.DataFrame)
                        else _pd.DataFrame()
                    )
                    r = None
                    if t2_x in d.columns and t2_y in d.columns:
                        x2 = _pd.to_numeric(d[t2_x], errors="coerce")
                        y2 = _pd.to_numeric(d[t2_y], errors="coerce")
                        r = float(x2.corr(y2)) if len(d) >= 2 else None
                    md["meta"] = {
                        "x": t2_x,
                        "y": t2_y,
                        "color": t2_color,
                        "stats": _basic_stats(d, [t2_x, t2_y]),
                        "correlation_r": r,
                    }
                except Exception:
                    md["meta"] = {"x": t2_x, "y": t2_y, "color": t2_color}
                selected_data["t2-graph-dyn"] = md
        # Tab 3 mapping (store UNFILTERED datasets for LLM)
        else:
            # Build both full (unfiltered) and chart (global+local filtered) datasets
            q1_t3_full, q2_t3_full, q3_t3_full, q4_t3_full = t3_get_filtered_frames(
                data_dict_3 or {}, {}
            )

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
                "outlet_categories": combine(
                    gf.get("outlet_categories"), lf.get("outlet_categories")
                ),
                "regions": list(gf.get("regions", [])),
                "sales_center_codes": list(lf.get("sales_center_codes", [])),
                "shortfall_side": lf.get("shortfall_side"),
                "kpi_focus": lf.get("kpi_focus"),
                "search_text": gf.get("search_text", ""),
                "outlet_types": list(gf.get("outlet_types", [])),
            }
            q1_t3_chart, q2_t3_chart, q3_t3_chart, q4_t3_chart = t3_get_filtered_frames(
                data_dict_3 or {}, merged
            )
            id_map3 = {
                "btn-select-t3-1": ("t3-graph-1", q1_t3_full, q1_t3_chart),
                # Profiles should match the static pre-aggregated radar source
                "btn-select-t3-3": (
                    "t3-graph-2",
                    (data_dict_3 or {}).get(
                        "radar-chart-before-filtering-q2", pd.DataFrame()
                    ),
                    (data_dict_3 or {}).get(
                        "radar-chart-before-filtering-q2", pd.DataFrame()
                    ),
                ),
            }
            gid, df_full, df_chart = id_map3[triggered]
            toggle(gid, df_full, df_chart)
            # For the top Tab 3 chart, also include the alternate dataset (q2) for LLM when selected
            if gid == "t3-graph-1" and ("t3-graph-1" in selected_graphs):
                sd = selected_data.get(gid, {})
                # alt_full should reflect the pre-aggregated q2 table from data layer (sheet3)
                alt_unfiltered = (data_dict_3 or {}).get("q2", pd.DataFrame())
                sd["alt_full"] = pack_df(alt_unfiltered)
                # alt_chart uses the filtered radar-source table
                sd["alt_chart"] = pack_df(q2_t3_chart)

                # Add derived KPI gap table (what bar actually plots) as a third dataset
                def _gap_table(dframe: pd.DataFrame):
                    import pandas as _pd

                    if not isinstance(dframe, _pd.DataFrame) or dframe.empty:
                        return _pd.DataFrame(
                            columns=["outlet_category", "kpi", "gap_value"]
                        )
                    rows = []
                    cats = ["B", "C", "D"]
                    for col, disp in KPI_DISPLAY:
                        if col not in dframe.columns:
                            continue
                        try:
                            g = (
                                dframe[dframe["outlet_category"].isin(cats)]
                                .groupby("outlet_category")[col]
                                .mean()
                            )
                        except Exception:
                            continue
                        for cat in cats:
                            if cat in g and pd.notna(g[cat]):
                                rows.append(
                                    {
                                        "outlet_category": cat,
                                        "kpi": disp,
                                        "gap_value": float(g[cat]) - 100.0,
                                    }
                                )
                    return _pd.DataFrame(rows)

                sd["gap_full"] = pack_df(_gap_table(q1_t3_full))
                sd["gap_chart"] = pack_df(_gap_table(q1_t3_chart))
                # Meta: top absolute gaps and which categories included
                try:
                    import pandas as _pd

                    gdf = _gap_table(q1_t3_chart)
                    top = []
                    if isinstance(gdf, _pd.DataFrame) and not gdf.empty:
                        gdf["abs_gap"] = gdf["gap_value"].abs()
                        top = (
                            gdf.sort_values("abs_gap", ascending=False)
                            .head(5)[["kpi", "outlet_category", "gap_value"]]
                            .to_dict("records")
                        )
                    sd["meta"] = {
                        "chart_type": "diverging_bars",
                        "categories": ["B", "C", "D"],
                        "top_gaps": top,
                    }
                except Exception:
                    pass
                selected_data[gid] = sd

        def label(gid):
            return GRAPH_LABELS.get(gid, gid)

        if not selected_graphs:
            info = html.Div(
                "No charts selected yet.",
                style={"color": "#6b7280", "fontSize": "13px"},
            )
            # q1..q6 (6) + t2-dyn (1) + t3-1 (1) + t3-3 (1) = 9
            pressed = ["false"] * 9
            return selected_graphs, *pressed, selected_data, info

        # chip style
        def chip(text):
            return html.Span(
                text,
                style={
                    "display": "inline-block",
                    "padding": "4px 10px",
                    "margin": "6px 6px 0 0",
                    "backgroundColor": "#e8f0fe",
                    "border": "1px solid #d0e2ff",
                    "borderRadius": "9999px",
                    "fontSize": "12px",
                    "color": "#1e3a8a",
                    "fontWeight": 600,
                    "whiteSpace": "nowrap",
                },
            )

        chips = [chip(label(gid)) for gid in selected_graphs]
        info = html.Div(
            [
                html.Div(
                    f"Selected ({len(selected_graphs)})",
                    style={"fontWeight": 700, "fontSize": "13px"},
                ),
                html.Div(chips, style={"display": "flex", "flexWrap": "wrap"}),
            ]
        )

        # Build aria-pressed map for all select buttons
        btn_ids = [
            "q1",
            "q2",
            "q3",
            "q4",
            "q5",
            "q6",
            "t2-graph-dyn",
            "t3-graph-1",
            "t3-graph-2",
        ]
        pressed = [("true" if gid in selected_graphs else "false") for gid in btn_ids]

        return selected_graphs, *pressed, selected_data, info

    # ----- View-underlying-data tables (inline) -----
    @app.callback(
        # Tab 1 tables
        Output("table-q1", "children"),
        Output("table-q2", "children"),
        Output("table-q3", "children"),
        Output("table-q4", "children"),
        Output("table-q5", "children"),
        Output("table-q6", "children"),
        # Tab 2 table
        Output("table-t2-dyn", "children"),
        # Tab 3 tables
        Output("table-t3-1", "children"),
        Output("table-t3-2", "children"),
        Output("table-t3-3", "children"),
        # Pressed state for all view buttons
        Output("btn-view-q1", "aria-pressed"),
        Output("btn-view-q2", "aria-pressed"),
        Output("btn-view-q3", "aria-pressed"),
        Output("btn-view-q4", "aria-pressed"),
        Output("btn-view-q5", "aria-pressed"),
        Output("btn-view-q6", "aria-pressed"),
        Output("btn-view-t2-dyn", "aria-pressed"),
        Output("btn-view-t3-1", "aria-pressed"),
        Output("btn-view-t3-1-new", "aria-pressed"),
        Output("btn-view-t3-3", "aria-pressed"),
        # Inputs: all view buttons
        Input("btn-view-q1", "n_clicks"),
        Input("btn-view-q2", "n_clicks"),
        Input("btn-view-q3", "n_clicks"),
        Input("btn-view-q4", "n_clicks"),
        Input("btn-view-q5", "n_clicks"),
        Input("btn-view-q6", "n_clicks"),
        Input("btn-view-t2-dyn", "n_clicks"),
        Input("btn-view-t3-1", "n_clicks"),
        Input("btn-view-t3-1-new", "n_clicks"),
        Input("btn-view-t3-3", "n_clicks"),
        # States: filters
        State("filter-store", "data"),
        State("tab3-filter-store", "data"),
        State("t2-selected-region", "data"),
        # States: current table contents for toggling
        State("table-q1", "children"),
        State("table-q2", "children"),
        State("table-q3", "children"),
        State("table-q4", "children"),
        State("table-q5", "children"),
        State("table-q6", "children"),
        State("table-t2-dyn", "children"),
        State("table-t3-1", "children"),
        State("table-t3-2", "children"),
        State("table-t3-3", "children"),
        prevent_initial_call=True,
    )
    def show_underlying_tables(
        vq1,
        vq2,
        vq3,
        vq4,
        vq5,
        vq6,
        vt2dyn,
        vt3_1,
        vt3_1_new,
        vt3_3,
        filters,
        tab3_local,
        t2_selected_region,
        tq1,
        tq2,
        tq3,
        tq4,
        tq5,
        tq6,
        tt2dyn,
        tt3_1,
        tt3_2,
        tt3_3,
    ):
        triggered = ctx.triggered_id
        if triggered is None:
            raise PreventUpdate

        # Helper: build a DataTable from a DataFrame
        def table_from_df(df):
            import pandas as pd  # local import to avoid global dependency if not used elsewhere

            if df is None or isinstance(df, pd.DataFrame) and df.empty:
                return html.Div(
                    "No data to display.",
                    style={"color": "#6b7280", "fontSize": "13px", "marginTop": "6px"},
                )
            # Limit rows for UI responsiveness
            try:
                df = df.head(300)
            except Exception:
                pass
            columns = [{"name": str(c), "id": str(c)} for c in df.columns]
            return dash_table.DataTable(
                columns=columns,
                data=df.to_dict("records"),
                page_size=10,
                sort_action="native",
                filter_action="native",
                style_table={
                    "overflowX": "auto",
                    "marginTop": "6px",
                    "maxHeight": "50vh",
                    "overflowY": "auto",
                    "border": "1px solid #e5e7eb",
                    "borderRadius": "8px",
                },
                style_cell={
                    "fontFamily": "Roboto, sans-serif",
                    "fontSize": 12,
                    "padding": "8px",
                    "whiteSpace": "normal",
                    "height": "auto",
                    "textAlign": "left",
                },
                style_header={
                    "fontWeight": "bold",
                    "backgroundColor": "#f3f4f6",
                    "borderBottom": "1px solid #e5e7eb",
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#fafafa"},
                ],
                fixed_rows={"headers": True},
                style_as_list_view=True,
            )

        # Defaults: no update for all table outputs
        out = [no_update] * 10

        # Resolve filtered frames based on which section triggered
        if triggered.startswith("btn-view-q"):
            # Tab 1: all graphs are based on the same sheet1.q1 table
            df_q1, _df2, _df3, df_q4, df_q5 = t1_get_filtered_frames(
                tab1, (filters or {})
            )
            f = filters or {}
            regs = list(f.get("regions") or [])
            df_for_q3 = df_q4 if len(regs) == 1 else df_q1

            # Build unfiltered q2 dataset (rgn, category, count, pct) for view
            _q1_unf, df_q2_unf, _d3, _d4, _d5 = t1_get_filtered_frames(tab1, {})

            id_map = {
                "btn-view-q1": (0, df_q1, tq1),
                "btn-view-q2": (1, df_q2_unf, tq2),
                "btn-view-q3": (2, df_for_q3, tq3),
                "btn-view-q4": (3, df_q1, tq4),
                "btn-view-q5": (4, df_q1, tq5),
            }
            if triggered == "btn-view-q6":
                # Build aggregated counts by category
                detail = (
                    df_q4
                    if isinstance(df_q4, pd.DataFrame) and not df_q4.empty
                    else df_q1
                )
                try:
                    cat_col = (
                        "outlet_category"
                        if "outlet_category" in detail.columns
                        else ("Category" if "Category" in detail.columns else None)
                    )
                except Exception:
                    cat_col = None
                if cat_col:
                    try:
                        counts = (
                            detail[[cat_col]]
                            .dropna()
                            .groupby(cat_col, dropna=False)
                            .size()
                            .reset_index(name="count")
                        )
                        # Order A-D when applicable
                        try:
                            import pandas as _pd

                            counts[cat_col] = _pd.Categorical(
                                counts[cat_col],
                                categories=["A", "B", "C", "D"],
                                ordered=True,
                            )
                            counts = counts.sort_values(cat_col)
                        except Exception:
                            pass
                    except Exception:
                        counts = detail[[cat_col]].copy()
                    out[5] = None if tq6 else table_from_df(counts)
                else:
                    out[5] = None if tq6 else table_from_df(detail)
            else:
                idx, df, cur = id_map[triggered]
                out[idx] = None if cur else table_from_df(df)
        elif triggered == "btn-view-t2-dyn":
            # Match graph behavior: respect global filters; when drilling down, ignore the global region
            # and apply a normalized region filter after fetching the data.
            df_src = dict(filters or {})
            if t2_selected_region and "regions" in df_src:
                df_src.pop("regions", None)
            ret = t2_get_filtered_frames(tab2, df_src)
            q1_t2 = ret[0] if isinstance(ret, tuple) else ret
            if (
                t2_selected_region
                and isinstance(q1_t2, pd.DataFrame)
                and not q1_t2.empty
                and "rgn" in q1_t2.columns
            ):
                try:
                    sr = str(t2_selected_region).strip().casefold()
                    tmp = q1_t2.copy()
                    tmp["__r"] = tmp["rgn"].astype(str).str.strip().str.casefold()
                    q1_t2 = tmp[tmp["__r"] == sr].drop(columns=["__r"])
                except Exception:
                    q1_t2 = q1_t2[q1_t2["rgn"] == t2_selected_region]
            idx, df, cur = 6, q1_t2, tt2dyn
            out[idx] = None if cur else table_from_df(df)
        else:
            # Tab 3 buttons: ensure each toggles its own table independently
            if triggered == "btn-view-t3-1":
                # View complete data: show unfiltered q1
                df = (data_dict_3 or {}).get("q1", pd.DataFrame())
                out[7] = None if tt3_1 else table_from_df(df)
                out[8] = None
            elif triggered == "btn-view-t3-1-new":
                # View data: show q2 table from data layer (pre-aggregated / sheet3)
                df = (data_dict_3 or {}).get("q2", pd.DataFrame())
                out[8] = None if tt3_2 else table_from_df(df)
                out[7] = None
            elif triggered == "btn-view-t3-3":
                # Profiles: show pre-aggregated radar-source table before filtering
                df = (data_dict_3 or {}).get(
                    "radar-chart-before-filtering-q2", pd.DataFrame()
                )
                out[9] = None if tt3_3 else table_from_df(df)

        # Build final visibility/pressed states for each table button
        current_tables = [
            tq1,
            tq2,
            tq3,
            tq4,
            tq5,
            tq6,  # 0..5
            tt2dyn,  # 6
            tt3_1,  # 7
            tt3_2,  # 8
            tt3_3,  # 9
        ]
        # Apply updated ones
        final_tables = [
            (out[i] if out[i] is not no_update else current_tables[i])
            for i in range(10)
        ]
        # Pressed sequence: q1..q6, t2-dyn, t3-1 (q1 table), t3-1-new (q2 table), t3-3
        pressed = [
            ("true" if final_tables[0] is not None else "false"),
            ("true" if final_tables[1] is not None else "false"),
            ("true" if final_tables[2] is not None else "false"),
            ("true" if final_tables[3] is not None else "false"),
            ("true" if final_tables[4] is not None else "false"),
            ("true" if final_tables[5] is not None else "false"),
            ("true" if final_tables[6] is not None else "false"),
            ("true" if final_tables[7] is not None else "false"),
            ("true" if final_tables[8] is not None else "false"),
            ("true" if final_tables[9] is not None else "false"),
        ]

        return tuple(out + pressed)

    # ----- Tab 2: dynamic correlation scatter -----

    # Tab 2: dynamic parameter correlation scatter
    @app.callback(
        Output("t2-graph-dynamic", "figure"),
        Input("filter-store", "data"),
        Input("t2-x-param", "value"),
        Input("t2-y-param", "value"),
        Input("t2-color-dim", "value"),
        Input("t2-selected-region", "data"),
    )
    def update_tab2_dynamic_scatter(filters, xcol, ycol, color_dim, t2_selected_region):
        import plotly.express as px
        from utils.colors import (
            category_color_map,
            brand_palette,
            color_map_from_list,
            diverse_palette,
        )
        import re
        import numpy as _np
        import pandas as _pd

        # Use global filters directly; we will optionally apply a local region refinement below
        df_src = dict(filters or {})
        df_tuple = t2_get_filtered_frames(tab2, df_src)
        df = df_tuple[0] if isinstance(df_tuple, tuple) else df_tuple
        fig = px.scatter(
            title=GRAPH_LABELS.get("t2-graph-dyn", "Explore Parameter Relationships")
        )
        if df is None or df.empty:
            fig.add_annotation(
                text="No data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(margin=dict(t=24), height=600)
            return fig
        # Normalize outlet name
        if "outlet_name" not in df.columns and "sales_outlet" in df.columns:
            df = df.rename(columns={"sales_outlet": "outlet_name"})
        # Normalize region text (trim/casefold) to make filtering robust
        if "rgn" in df.columns:
            try:
                df["rgn"] = df["rgn"].astype(str).str.strip()
            except Exception:
                pass

        # Robust numeric coercion: handle strings like "85%", "85.0", or with commas
        def _coerce_numeric_col(dframe, col):
            if col not in dframe.columns:
                return
            s = dframe[col]
            try:
                import pandas as _pd

                if not _pd.api.types.is_numeric_dtype(s):
                    s2 = (
                        s.astype(str)
                        .str.replace("%", "", regex=False)
                        .str.replace(",", "", regex=False)
                    )
                    # extract the first numeric token
                    s2 = s2.str.extract(r"([-+]?\d*\.?\d+)")[0]
                    dframe[col] = _pd.to_numeric(s2, errors="coerce")
                else:
                    # already numeric
                    pass
            except Exception:
                try:
                    dframe[col] = pd.to_numeric(s, errors="coerce")
                except Exception:
                    pass

        _coerce_numeric_col(df, xcol)
        _coerce_numeric_col(df, ycol)
        # Validate requested columns exist
        valid = xcol in df.columns and ycol in df.columns
        if not valid:
            fig.add_annotation(
                text="Selected columns not present in data",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(margin=dict(t=24), height=600)
            return fig

        # Always show outlet-level points; refine to selected region(s) if present
        regs = list((filters or {}).get("regions") or [])
        d = df.copy()
        # If a local region is selected (click), override to that single region
        if t2_selected_region and "rgn" in d.columns:

            def _norm(s):
                try:
                    return re.sub(r"\s+", " ", str(s).strip().casefold())
                except Exception:
                    return str(s)

            sr = _norm(t2_selected_region)
            try:
                d["__r"] = d["rgn"].astype(str).str.strip().str.casefold()
                d = d[d["__r"] == sr].drop(columns=["__r"])
            except Exception:
                d = d[d["rgn"] == t2_selected_region]
            title_suffix = f" — {t2_selected_region}"
        else:
            # If global regions are selected, restrict to them (supports multiple)
            if regs and "rgn" in d.columns:
                d = d[d["rgn"].isin(regs)]
                title_suffix = f" — Regions: {', '.join(map(str, regs))}"
            else:
                title_suffix = ""

        _coerce_numeric_col(d, xcol)
        _coerce_numeric_col(d, ycol)
        try:
            d = d.dropna(subset=[xcol, ycol])
        except Exception:
            pass

        # Build color mapping according to selected legend
        color_dim = color_dim or "outlet_category"
        hover_cols = (
            ["outlet_name", "rgn"]
            if "outlet_name" in d.columns
            else ["sales_outlet", "rgn"]
        )
        if color_dim in d.columns:
            if color_dim == "outlet_category":
                cmap = category_color_map()
            elif color_dim == "rgn":
                # Stable colors using all regions
                keys = list(all_regions or [])
                if not keys:
                    keys = d["rgn"].dropna().unique().tolist()
                cmap = color_map_from_list(keys, palette=brand_palette)
            else:
                # outlet_type or others – stabilize using full known list when available
                if color_dim == "outlet_type":
                    keys = list(all_outlet_types or [])
                    if not keys:
                        keys = d[color_dim].astype(str).dropna().unique().tolist()
                else:
                    keys = d[color_dim].astype(str).dropna().unique().tolist()
                cmap = color_map_from_list(keys, palette=diverse_palette)
            color_arg = color_dim
            hover_cols.append(color_dim)
        else:
            color_arg = "outlet_category" if "outlet_category" in d.columns else None
            cmap = category_color_map() if color_arg == "outlet_category" else None
            if color_arg:
                hover_cols.append(color_arg)

        # Ensure custom_data carries region and both categorical dimensions for downstream filtering
        cd_cols = []
        cd_cols.append("outlet_name" if "outlet_name" in d.columns else "sales_outlet")
        if "rgn" in d.columns:
            cd_cols.append("rgn")
        if "outlet_category" in d.columns:
            cd_cols.append("outlet_category")
        if "outlet_type" in d.columns:
            cd_cols.append("outlet_type")

        fig = px.scatter(
            d,
            x=xcol,
            y=ycol,
            color=color_arg,
            hover_data=hover_cols,
            title=GRAPH_LABELS.get("t2-graph-dyn", "Explore Parameter Relationships")
            + title_suffix,
            labels={xcol: xcol, ycol: ycol},
            custom_data=cd_cols,
            color_discrete_map=cmap,
        )
        fig.update_traces(
            marker=dict(size=10, opacity=0.9, line=dict(width=1, color="#ffffff"))
        )
        # Correlation across outlets in current view
        try:
            x2 = _pd.to_numeric(d[xcol], errors="coerce")
            y2 = _pd.to_numeric(d[ycol], errors="coerce")
            mask = x2.notna() & y2.notna()
            x2, y2 = x2[mask], y2[mask]
            r = float(x2.corr(y2)) if len(x2) >= 2 else _np.nan
            fig.update_layout(
                title=GRAPH_LABELS.get(
                    "t2-graph-dyn", "Explore Parameter Relationships"
                )
                + f"{title_suffix} (r={r:.2f}, n={len(x2)})"
            )
        except Exception:
            pass

        # Threshold lines removed per request
        fig.update_layout(margin=dict(t=24), height=600, showlegend=True)
        return fig

    # Tab 2: keep drilldown local — set selected region in a local store, do not change global filters
    @app.callback(
        Output("t2-selected-region", "data"),
        Input("t2-graph-dynamic", "clickData"),
        State("t2-selected-region", "data"),
        prevent_initial_call=True,
    )
    def set_t2_selected_region(click, current):
        if not click:
            raise PreventUpdate
        try:
            point = click.get("points", [{}])[0]
            cd = point.get("customdata") or []
        except Exception:
            cd = []
        # Extract region from customdata: [rgn] at region level; [outlet_name, rgn] at outlet level
        region = None
        if cd:
            if len(cd) == 1 and cd[0]:
                region = str(cd[0]).strip()
            elif len(cd) >= 2 and cd[1]:
                region = str(cd[1]).strip()
        # Fallback: region name might be in point text label for region-level scatter
        if not region:
            try:
                txt = point.get("text")
                if isinstance(txt, str) and txt.strip():
                    region = txt.strip()
            except Exception:
                pass
        if not region:
            raise PreventUpdate
        # Toggle behavior: clicking same region clears selection
        return None if (current == region) else region

    # ----- Tab 3: Five-Chart Dashboard figures -----
    @app.callback(
        Output("t3-graph-1", "figure"),
        Output("t3-graph-2", "figure"),
        Output("t3-graph-2-2s", "figure"),
        Output("t3-graph-2-1p2s", "figure"),
        Output("t3-graph-2-3s", "figure"),
        Input("filter-store", "data"),
        Input("tab3-filter-store", "data"),
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
            "outlet_categories": combine(
                gf.get("outlet_categories"), lf.get("outlet_categories")
            ),
            "regions": list(gf.get("regions", [])),
            "sales_center_codes": list(lf.get("sales_center_codes", [])),
            "shortfall_side": lf.get("shortfall_side"),
            "kpi_focus": lf.get("kpi_focus"),
            "search_text": gf.get("search_text", ""),
            "outlet_types": list(gf.get("outlet_types", [])),
        }
        figs = build_tab3_figures(
            data_dict_3 or {},
            merged,
            outlet_color_map=outlet_color_map,
            tier_colors=tier_color_map(),
            all_outlet_categories=all_outlet_categories,
            labels=GRAPH_LABELS,
            scatter_color_map=scatter_color_map,
        )
        # Return bar + 4 radars
        return figs[0], figs[1], figs[2], figs[3], figs[4]

    # Tab 3 cross-filtering controller
    @app.callback(
        Output("tab3-filter-store", "data"),
        Input("t3-graph-1", "clickData"),
        State("tab3-filter-store", "data"),
        prevent_initial_call=True,
    )
    def update_tab3_filters(c1, current):
        current = dict(
            current
            or {
                "outlet_categories": [],
                "sales_center_codes": [],
                "shortfall_side": None,
                "kpi_focus": None,
                "kpi_group": None,
            }
        )
        trig_id = ctx.triggered_id
        if trig_id is None:
            raise PreventUpdate
        newf = current.copy()

        def get_first_point(click):
            try:
                return (click or {}).get("points", [{}])[0]
            except Exception:
                return None

        def toggle_single(cur_list, val):
            cur = list(cur_list or [])
            if val is None:
                return cur
            return [] if (len(cur) == 1 and cur[0] == val) else [val]

        if trig_id == "t3-graph-1":
            # Click a bar segment to toggle selected outlet_category (B/C/D)
            point = get_first_point(c1)
            try:
                cat = (point.get("customdata") or [None])[0]
            except Exception:
                cat = None
            if cat is not None:
                newf["outlet_categories"] = toggle_single(
                    newf.get("outlet_categories"), cat
                )
        # No other Tab 3 interactions
        return newf

    return app


if __name__ == "__main__":
    try:
        if os.environ.get("DASH_OFFLINE", "0") == "1":
            # Offline/dev mode: skip DB calls and start app with empty datasets
            data_dict = _ensure_tab1_defaults({})
            data_dict_tab2 = {}
            data_dict_tab3 = {}
        else:
            data_dict = get_tab1_results()
            data_dict_tab2 = get_tab2_results()
            data_dict_tab3 = get_tab3_results()
        app = create_dashboard(data_dict, data_dict_tab2, data_dict_tab3)
        app.run(debug=True, port=8090)
    except ImportError:
        print("Error: Could not import 'get_tab1_results' from 'data_layer.tab_1'.")
        print(
            "Please ensure the file exists and the 'src' directory is in your Python path."
        )
    except Exception as e:
        print(f"An error occurred during app setup: {e}")
