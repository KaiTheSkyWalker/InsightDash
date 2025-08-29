from dash import dcc, html


def get_layout():
    """Return Tab 2 layout containing five graphs (q1..q4b) with select buttons."""
    btn_style = {'marginTop': '6px'}
    wrap_style = {'width': '98%', 'display': 'inline-block', 'verticalAlign': 'top'}
    return html.Div([
        html.Div([
            dcc.Graph(id='t2-graph-q1'),
            html.Button("Select this graph", id='btn-select-t2-q1', n_clicks=0, style=btn_style)
        ], style=wrap_style),
        html.Div([
            dcc.Graph(id='t2-graph-q2'),
            html.Button("Select this graph", id='btn-select-t2-q2', n_clicks=0, style=btn_style)
        ], style=wrap_style),
        html.Div([
            dcc.Graph(id='t2-graph-q3'),
            html.Button("Select this graph", id='btn-select-t2-q3', n_clicks=0, style=btn_style)
        ], style=wrap_style),
        html.Div([
            dcc.Graph(id='t2-graph-q4a'),
            html.Button("Select this graph", id='btn-select-t2-q4a', n_clicks=0, style=btn_style)
        ], style=wrap_style),
        html.Div([
            dcc.Graph(id='t2-graph-q4b'),
            html.Button("Select this graph", id='btn-select-t2-q4b', n_clicks=0, style=btn_style)
        ], style=wrap_style),
    ], style={'paddingTop': '10px'})
