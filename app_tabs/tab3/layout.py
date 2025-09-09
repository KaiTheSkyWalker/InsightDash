from dash import dcc, html


def get_layout():
    """Return Tab 3 layout for Alternative 1 (Compare & Rank).

    - Chart 1: Grouped weekly bars by category
    - Chart 2: Quadrant scatter
    - Chart 3: 100% stacked tier contribution
    - Chart 4 area: KPI cards + Top performers DataTable
    - Chart 5: Treemap (kept)
    """
    return html.Div([
        # Row 1
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Regional Value & Ops Metrics", className='graph-title'),
                    html.Div([
                        html.Button("Select this graph", id='btn-select-t3-1', n_clicks=0),
                        html.Button("View data", id='btn-view-t3-1', n_clicks=0, style={'marginLeft': '8px'})
                    ], className='graph-actions-row')
                ], className='graph-header'),
                dcc.Graph(id='t3-graph-1'),
                html.Div(id='table-t3-1')
            ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            html.Div([
                html.Div([
                    html.Div("Category Value & Ops Metrics", className='graph-title'),
                    html.Div([
                        html.Button("Select this graph", id='btn-select-t3-2', n_clicks=0),
                        html.Button("View data", id='btn-view-t3-2', n_clicks=0, style={'marginLeft': '8px'})
                    ], className='graph-actions-row')
                ], className='graph-header'),
                dcc.Graph(id='t3-graph-2'),
                html.Div(id='table-t3-2')
            ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ]),

        # Row 2
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Region × Category (Quality Index)", className='graph-title'),
                    html.Div([
                        html.Button("Select this graph", id='btn-select-t3-3', n_clicks=0),
                        html.Button("View data", id='btn-view-t3-3', n_clicks=0, style={'marginLeft': '8px'})
                    ], className='graph-actions-row')
                ], className='graph-header'),
                dcc.Graph(id='t3-graph-3'),
                html.Div(id='table-t3-3')
            ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            html.Div([
                html.Div([
                    html.Div("Top Service Outlets by Intake Units", className='graph-title'),
                    html.Div([
                        html.Button("Select this graph", id='btn-select-t3-4', n_clicks=0),
                        html.Button("View data", id='btn-view-t3-4', n_clicks=0, style={'marginLeft': '8px'})
                    ], className='graph-actions-row')
                ], className='graph-header'),
                dcc.Graph(id='t3-graph-4'),
                html.Div(id='table-t3-4')
            ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ], style={'marginTop': '10px'}),

        # Row 3
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Service CS% vs QPI%", className='graph-title'),
                    html.Div([
                        html.Button("Select this graph", id='btn-select-t3-5', n_clicks=0),
                        html.Button("View data", id='btn-view-t3-5', n_clicks=0, style={'marginLeft': '8px'})
                    ], className='graph-actions-row')
                ], className='graph-header'),
                dcc.Graph(id='t3-graph-5'),
                html.Div(id='table-t3-5')
            ]),
        ], style={'width': '98%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '10px'}),
    ], style={'paddingTop': '10px'})
