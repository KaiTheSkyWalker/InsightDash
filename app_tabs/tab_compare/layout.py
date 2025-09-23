from dash import dcc, html
from app_tabs.tab3.figures import KPI_DISPLAY


def get_layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("Monthly KPI Trend", className="graph-title"),
                        ],
                        className="graph-header",
                    ),
                    html.Div(
                        [
                            html.Label("KPI", style={"fontWeight": "600"}),
                            dcc.Dropdown(
                                id="compare-kpi",
                                options=[{"label": disp, "value": col} for col, disp in KPI_DISPLAY],
                                value=KPI_DISPLAY[0][0] if KPI_DISPLAY else None,
                                clearable=False,
                            ),
                        ],
                        style={"marginBottom": "12px"},
                    ),
                    dcc.Graph(id="compare-bar"),
                ],
                className="dashboard-card",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "Category Summary (Avg %, Δ)",
                                className="graph-title",
                            ),
                        ],
                        className="graph-header",
                    ),
                    dcc.Loading(
                        dcc.Graph(id="compare-table", figure={}), type="dot"
                    ),
                ],
                className="dashboard-card",
            ),
        ]
    )
