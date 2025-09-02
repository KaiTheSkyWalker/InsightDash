from dash import dcc, html


def get_layout():
    """Return Tab 2 layout containing five graphs (q1..q4b) with select buttons."""
    btn_style = {'marginTop': '6px'}
    wrap_style = {'width': '98%', 'display': 'inline-block', 'verticalAlign': 'top'}
    return html.Div([
        html.Div([
            dcc.Graph(id='t2-graph-q1'),
            html.Div([
                html.Button("Select this graph", id='btn-select-t2-q1', n_clicks=0, style=btn_style),
                html.Button("View data", id='btn-view-t2-q1', n_clicks=0, style={'marginTop': '6px', 'marginLeft': '8px'})
            ]),
            html.Div(id='table-t2-q1')
        ], style=wrap_style),
        html.Div([
            dcc.Graph(id='t2-graph-q2'),
            html.Div([
                html.Button("Select this graph", id='btn-select-t2-q2', n_clicks=0, style=btn_style),
                html.Button("View data", id='btn-view-t2-q2', n_clicks=0, style={'marginTop': '6px', 'marginLeft': '8px'})
            ]),
            html.Div(id='table-t2-q2')
        ], style=wrap_style),
        html.Div([
            dcc.Graph(id='t2-graph-q3'),
            html.Div([
                html.Button("Select this graph", id='btn-select-t2-q3', n_clicks=0, style=btn_style),
                html.Button("View data", id='btn-view-t2-q3', n_clicks=0, style={'marginTop': '6px', 'marginLeft': '8px'})
            ]),
            html.Div(id='table-t2-q3')
        ], style=wrap_style),
        html.Div([
            dcc.Graph(id='t2-graph-q4a'),
            html.Div([
                html.Button("Select this graph", id='btn-select-t2-q4a', n_clicks=0, style=btn_style),
                html.Button("View data", id='btn-view-t2-q4a', n_clicks=0, style={'marginTop': '6px', 'marginLeft': '8px'})
            ]),
            html.Div(id='table-t2-q4a')
        ], style=wrap_style),
        html.Div([
            dcc.Graph(id='t2-graph-q4b'),
            html.Div([
                html.Button("Select this graph", id='btn-select-t2-q4b', n_clicks=0, style=btn_style),
                html.Button("View data", id='btn-view-t2-q4b', n_clicks=0, style={'marginTop': '6px', 'marginLeft': '8px'})
            ]),
            html.Div(id='table-t2-q4b')
        ], style=wrap_style),
    ], style={'paddingTop': '10px'})
