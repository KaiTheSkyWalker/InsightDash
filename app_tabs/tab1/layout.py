from dash import dcc, html


def get_layout():
    """Return Tab 1 layout containing five graphs and select buttons."""
    return html.Div([
        html.Div([
            dcc.Graph(id='graph-q1'),
            html.Div([
                html.Button("Select this graph", id='btn-select-q1', n_clicks=0, style={'marginTop': '6px'}),
                html.Button("View data", id='btn-view-q1', n_clicks=0, style={'marginTop': '6px', 'marginLeft': '8px'})
            ]),
            html.Div(id='table-q1')
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            dcc.Graph(id='graph-q2'),
            html.Div([
                html.Button("Select this graph", id='btn-select-q2', n_clicks=0, style={'marginTop': '6px'}),
                html.Button("View data", id='btn-view-q2', n_clicks=0, style={'marginTop': '6px', 'marginLeft': '8px'})
            ]),
            html.Div(id='table-q2')
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            dcc.Graph(id='graph-q3'),
            html.Div([
                html.Button("Select this graph", id='btn-select-q3', n_clicks=0, style={'marginTop': '6px'}),
                html.Button("View data", id='btn-view-q3', n_clicks=0, style={'marginTop': '6px', 'marginLeft': '8px'})
            ]),
            html.Div(id='table-q3')
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            dcc.Graph(id='graph-q4'),
            html.Div([
                html.Button("Select this graph", id='btn-select-q4', n_clicks=0, style={'marginTop': '6px'}),
                html.Button("View data", id='btn-view-q4', n_clicks=0, style={'marginTop': '6px', 'marginLeft': '8px'})
            ]),
            html.Div(id='table-q4')
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            dcc.Graph(id='graph-q5'),
            html.Div([
                html.Button("Select this graph", id='btn-select-q5', n_clicks=0, style={'marginTop': '6px'}),
                html.Button("View data", id='btn-view-q5', n_clicks=0, style={'marginTop': '6px', 'marginLeft': '8px'})
            ]),
            html.Div(id='table-q5')
        ], style={'width': '98%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ])
