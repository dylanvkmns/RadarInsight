import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import sqlite3
import plotly.graph_objs as go

LINES_MARKERS = 'lines+markers'

DATA_DB = "rqmData.db"


# Database functions
def get_all_radars():
    conn = sqlite3.connect(DATA_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Radar_Name FROM biases")
    radars = cursor.fetchall()
    conn.close()
    return [{'label': radar[0], 'value': radar[0]} for radar in radars]


def get_all_stats():
    return [
        {
            'label': 'pdP',
            'value': 'pdP'
        },
        {
            'label': 'pdS',
            'value': 'pdS'
        },
        {
            'label': 'pdM',
            'value': 'pdM'
        },
        {
            'label': 'pdPS',
            'value': 'pdPS'
        },
        {
            'label': 'pdPM',
            'value': 'pdPM'
        },
        {
            'label': 'Range Bias',
            'value': 'Range_Bias'
        },  # Assuming you have columns named 'Bias1', 'Bias2', etc.
        {
            'label': 'Azimuth Bias',
            'value': 'Azimuth_Bias'
        },
        {
            'label': 'Time Bias',
            'value': 'Time_Bias'
        },
        # Add other biases as needed
    ]


# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Radar Statistics"

app.layout = html.Div(style={
    'backgroundColor': '#EAEDED',
    'fontFamily': 'Tahoma'
},
    children=[
        html.H1("Radar Statistics",
                style={
                    'textAlign': 'center',
                    'paddingTop': '20px',
                    'color': '#34495E'
                }),
        dcc.Tabs(id="tabs",
                 value='tab-1',
                 children=[
                     dcc.Tab(label='Bias', value='tab-1'),
                     dcc.Tab(label='Probability',
                             value='tab-2'),
                     dcc.Tab(label='Comparison',
                             value='tab-3'),
                     dcc.Tab(label='Overview', value='tab-4')
                 ]),
        html.Div(id='tabs-content')
    ])


@app.callback(Output('tabs-content', 'children'), Input('tabs', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            dcc.Dropdown(id='radar-dropdown', options=get_all_radars()),
            dcc.Graph(id='bias-graph')
        ])
    elif tab == 'tab-2':
        return html.Div([
            dcc.Dropdown(id='radar-dropdown-prob', options=get_all_radars()),
            dcc.Graph(id='probability-graph')
        ])
    elif tab == 'tab-3':
        return html.Div([
            dcc.Dropdown(id='stat-dropdown', options=get_all_stats()),
            dcc.Graph(id='comparison-graph')
        ])
    elif tab == 'tab-4':
        return html.Div(id='overview-content')


# Callbacks for graphs and other components:


@app.callback(Output('bias-graph', 'figure'),
              [Input('radar-dropdown', 'value')])
def update_bias_figure(selected_radar):
    conn = sqlite3.connect(DATA_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM biases WHERE Radar_Name=?",
                   (selected_radar,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return go.Figure()

    labels = [desc[0] for desc in cursor.description
              ][2:-1]  # Exclude Radar_Name, Antenna_Type and Job_Date
    dates = [entry[-1] for entry in data]

    return {
        'data': [
            go.Scatter(x=dates,
                       y=[entry[i + 2] for entry in data],
                       mode=LINES_MARKERS,
                       name=label) for i, label in enumerate(labels)
        ],
        'layout':
            go.Layout(title=f"Bias for {selected_radar}")
    }


@app.callback(Output('probability-graph', 'figure'),
              [Input('radar-dropdown-prob', 'value')])
def update_probability_figure(selected_radar):
    conn = sqlite3.connect(DATA_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detection_rates WHERE ds_name=?",
                   (selected_radar,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return go.Figure()

    labels = [desc[0] for desc in cursor.description
              ][2:-1]  # Exclude ds_name, ds_type, and Job_Date
    dates = [entry[-1] for entry in data]

    return {
        'data': [go.Scatter(x=dates, y=[entry[i+2] for entry in data], mode='lines+markers', name=label) for i, label in enumerate(labels)],
        'layout': go.Layout(title=f"Probability for {selected_radar}", yaxis=dict(range=[0, 100]))
    }


@app.callback(Output('comparison-graph', 'figure'),
              [Input('stat-dropdown', 'value')])
def update_comparison_figure(selected_stat):
    if not selected_stat:
        raise dash.exceptions.PreventUpdate

    conn = sqlite3.connect(DATA_DB)
    cursor = conn.cursor()

    if "Bias" in selected_stat:  # Check if the selected_stat is a bias
        table_name = "biases"
        radar_column = "Radar_Name"
    else:
        table_name = "detection_rates"
        radar_column = "ds_name"

    cursor.execute(
        f"SELECT {radar_column}, {selected_stat}, Job_Date FROM {table_name} ORDER BY Job_Date"
    )
    data = cursor.fetchall()
    conn.close()

    radar_names = list(set([entry[0] for entry in data]))
    radar_data = {radar: [] for radar in radar_names}
    dates = list(set([entry[-1] for entry in data]))

    for entry in data:
        radar_data[entry[0]].append(entry[1])

    return {
        'data': [
            go.Scatter(x=dates,
                       y=radar_data[radar],
                       mode=LINES_MARKERs,
                       name=radar) for radar in radar_names
        ],
        'layout':
            go.Layout(title=f"Comparison for {selected_stat}")
    }


@app.callback(Output('overview-content', 'children'), [Input('tabs', 'value')])
def update_overview_figure(tab):
    if tab != 'tab-4':
        raise dash.exceptions.PreventUpdate

    conn = sqlite3.connect(DATA_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Radar_Name FROM biases")
    radars = [radar[0] for radar in cursor.fetchall()]

    radar_graphs = []
    for idx, radar in enumerate(radars):
        cursor.execute("SELECT * FROM detection_rates WHERE ds_name=?",
                       (radar,))
        radar_data = cursor.fetchall()

        if radar_data:
            labels = [desc[0] for desc in cursor.description][2:-1]
            dates = [entry[-1] for entry in radar_data]
            traces = [
                go.Scatter(x=dates,
                           y=[entry[i + 2] for entry in radar_data],
                           mode=LINES_MARKERS,
                           name=label) for i, label in enumerate(labels)
            ]

            radar_graph = html.Div(
                dcc.Graph(id=f'overview-{radar}',
                          figure={
                              'data': traces,
                              'layout': go.Layout(title=f"{radar}'s Stats")
                          }),
                style={
                    'width': '50%',
                    'display': 'inline-block'
                }
                # Adjust the width to slightly less than 50% to account for padding/margins
            )
            radar_graphs.append(radar_graph)

            # If index is odd (second graph in the pair), or it's the last graph, wrap the graphs in a row
            if idx % 2 == 1 or idx == len(radars) - 1:
                radar_graphs[-2:] = [
                    html.Div(radar_graphs[-2:],
                             style={
                                 'width': '100%',
                                 'display': 'inline-block'
                             })
                ]

    conn.close()
    return radar_graphs


if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
