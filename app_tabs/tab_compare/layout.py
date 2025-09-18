from dash import dcc, html
from app_tabs.tab3.figures import KPI_DISPLAY


def get_layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("KPI"),
                            dcc.Dropdown(
                                id="compare-kpi",
                                options=[{"label": disp, "value": col} for col, disp in KPI_DISPLAY],
                                value=KPI_DISPLAY[0][0] if KPI_DISPLAY else None,
                                clearable=False,
                            ),
                        ],
                        style={"flex": "1", "marginRight": "10px"},
                    ),
                ],
                style={"display": "flex", "marginBottom": "8px"},
            ),
            dcc.Graph(id="compare-bar"),
            html.Hr(),
            html.Div(
                [
                    html.H4("Category Summary (Avg %)", style={"margin": "8px 0"}),
                    dcc.Loading(
                        dcc.Graph(id="compare-table", figure={}), type="dot"
                    ),
                ]
            ),
        ]
    )

