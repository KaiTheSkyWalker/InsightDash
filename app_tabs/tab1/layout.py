from dash import dcc, html


def get_layout():
    """Return Tab 1 layout with enlarged figures and drilldown area.

    - q1, q2, q3 are full-width and stacked for readability
    - q4 (Top Outlets) moved to the very bottom
    - A drilldown panel shows after clicking a region on q1/q3
    """
    full = {
        "width": "98%",
        "display": "inline-block",
        "verticalAlign": "top",
        "marginTop": "10px",
    }
    return html.Div(
        [
            # Drilldown panel hidden (no separate graph per spec)
            html.Div(
                id="tab1-drilldown",
                style={"width": "98%", "marginTop": "10px", "display": "none"},
            ),
            # q1 removed per spec (Average Total Score by Region)
            # q2 — big (Stacked bar)
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "Outlet Category Distribution (% by Region)",
                                        className="graph-title",
                                    ),
                                    html.Div(
                                        [
                                            html.Button(
                                                "Select this graph",
                                                id="btn-select-q2",
                                                n_clicks=0,
                                            ),
                                            html.Button(
                                                "View data",
                                                id="btn-view-q2",
                                                n_clicks=0,
                                            ),
                                        ],
                                        className="graph-actions-row",
                                    ),
                                ],
                                className="graph-header",
                            ),
                            dcc.Graph(id="graph-q2"),
                        ]
                    ),
                    html.Div(id="table-q2"),
                ],
                style=full,
            ),
            # q6 — Outlet Count by Category (A/B/C/D)
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "Number of Outlets by Category",
                                        className="graph-title",
                                    ),
                                    html.Div(
                                        [
                                            html.Button(
                                                "Select this graph",
                                                id="btn-select-q6",
                                                n_clicks=0,
                                            ),
                                            html.Button(
                                                "View data",
                                                id="btn-view-q6",
                                                n_clicks=0,
                                            ),
                                        ],
                                        className="graph-actions-row",
                                    ),
                                ],
                                className="graph-header",
                            ),
                            dcc.Graph(id="graph-q6"),
                        ]
                    ),
                    html.Div(id="table-q6"),
                ],
                style=full,
            ),
            # q3 — big
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "Performance vs. Quality by Region",
                                        className="graph-title",
                                    ),
                                    html.Div(
                                        [
                                            html.Button(
                                                "Select this graph",
                                                id="btn-select-q3",
                                                n_clicks=0,
                                            ),
                                            html.Button(
                                                "View data",
                                                id="btn-view-q3",
                                                n_clicks=0,
                                            ),
                                        ],
                                        className="graph-actions-row",
                                    ),
                                ],
                                className="graph-header",
                            ),
                            dcc.Graph(id="graph-q3"),
                        ]
                    ),
                    html.Div(id="table-q3"),
                ],
                style=full,
            ),
            # Hidden extras to keep callbacks stable (not visible)
            html.Div(
                [
                    html.Button("Select this graph", id="btn-select-q1", n_clicks=0),
                    html.Button("View data", id="btn-view-q1", n_clicks=0),
                    html.Button("Select this graph", id="btn-select-q4", n_clicks=0),
                    html.Button("View data", id="btn-view-q4", n_clicks=0),
                    html.Button("Select this graph", id="btn-select-q5", n_clicks=0),
                    html.Button("View data", id="btn-view-q5", n_clicks=0),
                    dcc.Graph(id="graph-q5"),
                    html.Div(id="table-q5"),
                    dcc.Graph(id="graph-q4"),
                    html.Div(id="table-q4"),
                    dcc.Graph(id="graph-q1"),
                    html.Div(id="table-q1"),
                ],
                style={"display": "none"},
            ),
        ],
        style={"paddingTop": "6px"},
    )
