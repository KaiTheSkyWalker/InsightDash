from dash import dcc, html


def get_layout():
    """Return Tab 1 layout containing five graphs and select buttons."""
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Regional Performance (Avg Score)", className='graph-title'),
                    html.Div([
                        html.Button("Select this graph", id='btn-select-q1', n_clicks=0),
                        html.Button("View data", id='btn-view-q1', n_clicks=0)
                    ], className='graph-actions-row')
                ], className='graph-header'),
                dcc.Graph(id='graph-q1'),
            ]),
            html.Div(id='table-q1')
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '10px'}),

        html.Div([
            html.Div([
                html.Div([
                    html.Div("Outlet Category Averages", className='graph-title'),
                    html.Div([
                        html.Button("Select this graph", id='btn-select-q2', n_clicks=0),
                        html.Button("View data", id='btn-view-q2', n_clicks=0)
                    ], className='graph-actions-row')
                ], className='graph-header'),
                dcc.Graph(id='graph-q2'),
            ]),
            html.Div(id='table-q2')
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '10px'}),

        html.Div([
            html.Div([
                html.Div([
                    html.Div("Region × Category (Avg Score)", className='graph-title'),
                    html.Div([
                        html.Button("Select this graph", id='btn-select-q3', n_clicks=0),
                        html.Button("View data", id='btn-view-q3', n_clicks=0)
                    ], className='graph-actions-row')
                ], className='graph-header'),
                dcc.Graph(id='graph-q3'),
            ]),
            html.Div(id='table-q3')
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '10px'}),

        html.Div([
            html.Div([
                html.Div([
                    html.Div("Top Outlets by Score", className='graph-title'),
                    html.Div([
                        html.Button("Select this graph", id='btn-select-q4', n_clicks=0),
                        html.Button("View data", id='btn-view-q4', n_clicks=0)
                    ], className='graph-actions-row')
                ], className='graph-header'),
                dcc.Graph(id='graph-q4'),
            ]),
            html.Div(id='table-q4')
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '10px'}),

        html.Div([
            html.Div([
                html.Div([
                    html.Div("Bottom Outlets by Score", className='graph-title'),
                    html.Div([
                        html.Button("Select this graph", id='btn-select-q5', n_clicks=0),
                        html.Button("View data", id='btn-view-q5', n_clicks=0)
                    ], className='graph-actions-row')
                ], className='graph-header'),
                dcc.Graph(id='graph-q5'),
            ]),
            html.Div(id='table-q5')
        ], style={'width': '98%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '10px'}),
    ], style={'paddingTop': '6px'})
