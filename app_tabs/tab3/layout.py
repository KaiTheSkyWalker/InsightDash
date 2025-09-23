from dash import dcc, html


def get_layout():
    """Tab 3 layout per spec: Category and Type Diagnostics.

    - Layer 1: Diverging Bar — full width
    - Layer 2: Radar (full width)
    """
    two_col_row = {
        "marginTop": "10px",
        "display": "flex",
        "gap": "18px",
        "flexWrap": "wrap",
    }
    split_card_style = {"flex": "1", "minWidth": "320px"}
    return html.Div(
        [
            dcc.Store(id="t3-active-table-store", data=None),
            # Layer 1: Diverging Bar (Category Overview)
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "What's Holding Back B, C, & D Outlets?",
                                        className="graph-title",
                                    ),
                                    html.Div(
                                        [
                                            html.Button(
                                                "Select this graph",
                                                id="btn-select-t3-1",
                                                n_clicks=0,
                                            ),
                                            # Distinct keys ensure Dash treats these as separate controls
                                            html.Button(
                                                "View complete data",
                                                id="btn-view-t3-1",
                                                n_clicks=0,
                                                key="t3-view-q1",
                                                style={"marginLeft": "8px"},
                                            ),
                                            html.Button(
                                                "View data",
                                                id="btn-view-t3-1-new",
                                                n_clicks=0,
                                                key="t3-view-q2",
                                                style={"marginLeft": "8px"},
                                            ),
                                        ],
                                        className="graph-actions-row",
                                    ),
                                ],
                                className="graph-header",
                            ),
                            dcc.Graph(id="t3-graph-1", style={"height": "520px"}),
                            # Two separate containers for the two datasets
                            html.Div(id="table-t3-1"),
                            html.Div(id="table-t3-2"),
                        ],
                        className="dashboard-card",
                    ),
                ]
            ),
            # Layer 2: Radar group header (overall title + buttons)
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "Outlet Type Capability Profiles",
                                        className="graph-title",
                                    ),
                                    html.Div(
                                        [
                                            html.Button(
                                                "Select this graph",
                                                id="btn-select-t3-3",
                                                n_clicks=0,
                                            ),
                                            html.Button(
                                                "View data",
                                                id="btn-view-t3-3",
                                                n_clicks=0,
                                                style={"marginLeft": "8px"},
                                            ),
                                        ],
                                        className="graph-actions-row",
                                    ),
                                ],
                                className="graph-header",
                            ),
                            # Independent table container for profiles section
                            html.Div(id="table-t3-3"),
                        ],
                        className="dashboard-card",
                    ),
                ],
                style={"marginTop": "10px"},
            ),
            # Layer 2: Radars (four outlet types)
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "1S — Average Performance Profile",
                                        className="graph-title",
                                    ),
                                ],
                                className="graph-header",
                            ),
                            dcc.Graph(id="t3-graph-2", style={"height": "520px"}),
                        ],
                        className="dashboard-card",
                        style=split_card_style,
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "2S — Average Performance Profile",
                                        className="graph-title",
                                    ),
                                ],
                                className="graph-header",
                            ),
                            dcc.Graph(id="t3-graph-2-2s", style={"height": "520px"}),
                        ],
                        className="dashboard-card",
                        style=split_card_style,
                    ),
                ],
                style=two_col_row,
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "1+2S — Average Performance Profile",
                                        className="graph-title",
                                    ),
                                ],
                                className="graph-header",
                            ),
                            dcc.Graph(id="t3-graph-2-1p2s", style={"height": "520px"}),
                        ],
                        className="dashboard-card",
                        style=split_card_style,
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "3S — Average Performance Profile",
                                        className="graph-title",
                                    ),
                                ],
                                className="graph-header",
                            ),
                            dcc.Graph(id="t3-graph-2-3s", style={"height": "520px"}),
                        ],
                        className="dashboard-card",
                        style=split_card_style,
                    ),
                ],
                style=two_col_row,
            ),
            # Remove supporting scatter and placeholders per new spec (two charts only)
        ],
        style={"paddingTop": "10px"},
    )
