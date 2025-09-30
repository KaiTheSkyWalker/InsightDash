from dash import dcc, html
from app_tabs.tab3.figures import KPI_DISPLAY


def get_layout():
    """Return Tab 2 layout with dynamic correlation scatter plus existing charts."""
    btn_style = {}
    return html.Div(
        [
            # Local store to keep Tab 2 selection independent from global filters
            dcc.Store(id="t2-selected-region", data=None),
            dcc.Store(id="t2-toast", data=None),
            # Dynamic parameter correlation controls + graph
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "Explore Parameter Relationships",
                                className="graph-title",
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        "Select this graph",
                                        id={"type": "select-btn", "graph": "t2-graph-dyn"},
                                        n_clicks=0,
                                        style=btn_style,
                                        className="graph-select-btn",
                                    ),
                                    html.Button(
                                        "View data",
                                        id="btn-view-t2-dyn",
                                        n_clicks=0,
                                        style={"marginLeft": "8px"},
                                    ),
                                ],
                                className="graph-actions-row",
                            ),
                        ],
                        className="graph-header",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label("X"),
                                    dcc.Dropdown(
                                        id="t2-x-param",
                                        options=[
                                            {
                                                "label": f"{label} %",
                                                "value": col,
                                            }
                                            for col, label in KPI_DISPLAY
                                        ],
                                        placeholder="Select parameter (X-axis)",
                                        value="cs_service_pct",
                                    ),
                                ],
                                style={
                                    "width": "32%",
                                    "display": "inline-block",
                                },
                            ),
                            html.Div(
                                [
                                    html.Label("Y"),
                                    dcc.Dropdown(
                                        id="t2-y-param",
                                        options=[
                                            {
                                                "label": f"{label} %",
                                                "value": col,
                                            }
                                            for col, label in KPI_DISPLAY
                                        ],
                                        placeholder="Select parameter (Y-axis)",
                                        value="revenue_pct",
                                    ),
                                ],
                                style={
                                    "width": "32%",
                                    "display": "inline-block",
                                },
                            ),
                            html.Div(
                                [
                                    html.Label("Legend"),
                                    dcc.Dropdown(
                                        id="t2-color-dim",
                                        options=[
                                            {"label": "Region", "value": "rgn"},
                                            {
                                                "label": "Outlet Category",
                                                "value": "outlet_category",
                                            },
                                            {
                                                "label": "Outlet Type",
                                                "value": "outlet_type",
                                            },
                                        ],
                                        placeholder="Color by... (Legend)",
                                        value="outlet_category",
                                    ),
                                ],
                                style={
                                    "width": "32%",
                                    "display": "inline-block",
                                },
                            ),
                        ],
                        style={
                            "margin": "8px 0",
                            "display": "flex",
                            "justifyContent": "space-between",
                        },
                    ),
                    dcc.Graph(
                        id="t2-graph-dynamic", style={"height": "620px"}
                    ),
                    html.Div(id="table-t2-dyn"),
                ],
                className="dashboard-card",
            ),
        ],
        style={"paddingTop": "10px"},
    )
