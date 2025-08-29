from dash import dcc, html


def get_layout():
    """Return Tab 1 layout containing five graphs and select buttons."""
    return html.Div([
        html.Div([
            dcc.Graph(id='graph-q1'),
            html.Button("Select this graph", id='btn-select-q1', n_clicks=0, style={'marginTop': '6px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            dcc.Graph(id='graph-q2'),
            html.Button("Select this graph", id='btn-select-q2', n_clicks=0, style={'marginTop': '6px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            dcc.Graph(id='graph-q3'),
            html.Button("Select this graph", id='btn-select-q3', n_clicks=0, style={'marginTop': '6px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            dcc.Graph(id='graph-q4'),
            html.Button("Select this graph", id='btn-select-q4', n_clicks=0, style={'marginTop': '6px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            dcc.Graph(id='graph-q5'),
            html.Button("Select this graph", id='btn-select-q5', n_clicks=0, style={'marginTop': '6px'})
        ], style={'width': '98%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ])

