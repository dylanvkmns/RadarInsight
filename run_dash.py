"""
This Dash application visualizes and analyzes radar statistics data stored in an SQLite database.
It provides interactive graphs and a report generation feature.
"""

import io
import sqlite3

import dash
from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

import pandas as pd
import plotly.graph_objs as go

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate

LINES_MARKERS = 'lines+markers'

DATA_DB = "rqmData.db"

# Database functions

conn = sqlite3.connect(DATA_DB)
cursor = conn.cursor()
cursor.execute("SELECT * FROM detection_rates")  # Adjust the query as needed
data = cursor.fetchall()
column_names = [desc[0] for desc in cursor.description]
df = pd.DataFrame(data, columns=column_names)
conn.close()

years = df['Job_Date'].unique()  # Assuming 'Job_Date' is your date column
radars = df['ds_name'].unique()


def get_all_radars():
    """Fetches a list of unique radar names from the database."""
    conn_radars = sqlite3.connect(DATA_DB)  # Use a different name here
    cursor = conn_radars.cursor()
    cursor.execute("SELECT DISTINCT Radar_Name FROM biases")
    radars = cursor.fetchall()
    conn_radars.close()
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
        },
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
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
# Theme is adjustable by changing dbc.themes.<themeName>, available themes are found here: https://hellodash.pythonanywhere.com/
app = dash.Dash(__name__, suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.JOURNAL, dbc_css])
app.title = "Radar Statistics"
load_figure_template("journal")


app.layout = dbc.Container(
    children=[
        html.H1("Radar Statistics"),

        dbc.Tabs(  # Use dbc.Tabs instead of dcc.Tabs
            id="tabs",
            active_tab='tab-1',  # Use active_tab instead of value
            children=[
                # Use tab_id instead of value
                dbc.Tab(label='Bias', tab_id='tab-1'),
                dbc.Tab(label='Probability', tab_id='tab-2'),
                dbc.Tab(label='Comparison', tab_id='tab-3'),
                dbc.Tab(label='Overview', tab_id='tab-4'),
                dbc.Tab(label='Report', tab_id='tab-5')
            ]
        ),

        html.Div(id='tabs-content')
    ],
    className="dbc"
)


# Use active_tab
@app.callback(Output('tabs-content', 'children'), [Input('tabs', 'active_tab')])
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            dbc.Select(  # Use dbc.Select instead of dcc.Dropdown
                id='radar-dropdown',
                options=get_all_radars()
            ),
            dcc.Graph(id='bias-graph')
        ])
    elif tab == 'tab-2':
        return html.Div([
            dbc.Select(
                id='radar-dropdown-prob',
                options=get_all_radars()
            ),
            dcc.Graph(id='probability-graph')
        ])
    elif tab == 'tab-3':
        return html.Div([
            dbc.Select(
                id='stat-dropdown',
                options=get_all_stats()
            ),
            dcc.Graph(id='comparison-graph')
        ])
    elif tab == 'tab-4':
        return html.Div(id='overview-content')
    elif tab == 'tab-5':  # Content for the "Report" tab
        return html.Div([
            dcc.DatePickerRange(
                id='date-range-picker',
                min_date_allowed=df['Job_Date'].min(),
                max_date_allowed=df['Job_Date'].max(),
                start_date=df['Job_Date'].min(),
                end_date=df['Job_Date'].max()
            ),
            dbc.Button("Generate Report", id='generate-report-button',
                       color="primary", className="m-2"),
            dcc.Download(id="download-report")
        ])

# Callbacks for graphs and other components


@app.callback(Output('bias-graph', 'figure'),
              [Input('radar-dropdown', 'value')])
def update_bias_figure(selected_radar):
    conn_bias = sqlite3.connect(DATA_DB)  # Use a different name here
    cursor = conn_bias.cursor()
    cursor.execute("SELECT * FROM biases WHERE Radar_Name=?", (selected_radar,))
    data = cursor.fetchall()
    conn_bias.close()

    if not data:
        return go.Figure()

    labels = [desc[0] for desc in cursor.description][2:-1]
    dates = [entry[-1] for entry in data]

    return {
        'data': [
            go.Scatter(x=dates,
                       y=[entry[i + 2] for entry in data],
                       mode=LINES_MARKERS,
                       name=label) for i, label in enumerate(labels)
        ],
        'layout': go.Layout(title=f"Bias for {selected_radar}")
    }


@app.callback(Output('probability-graph', 'figure'),
              [Input('radar-dropdown-prob', 'value')])
def update_probability_figure(selected_radar):
    conn = sqlite3.connect(DATA_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM detection_rates WHERE ds_name=?", (selected_radar,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return go.Figure()

    labels = [desc[0] for desc in cursor.description][2:-1]
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

    if "Bias" in selected_stat:
        table_name = "biases"
        radar_column = "Radar_Name"
    else:
        table_name = "detection_rates"
        radar_column = "ds_name"

    # Modify the query to handle Job_Date as a DATE and ensure sorting
    cursor.execute(
        f"SELECT {radar_column}, {selected_stat}, Job_Date FROM {
            table_name} ORDER BY Job_Date"
    )
    data = cursor.fetchall()
    conn.close()

    radar_names = list(set([entry[0] for entry in data]))

    # Initialize radar_data with None values for all dates
    dates = sorted(list({entry[-1] for entry in data}))
    radar_data = {radar: [None] * len(dates) for radar in radar_names}

    # Populate radar_data with values, ensuring alignment with dates
    for entry in data:
        radar, value, date = entry
        date_index = dates.index(date)
        radar_data[radar][date_index] = value

    return {
        'data': [
            go.Scatter(x=dates,
                       y=radar_data[radar],
                       mode=LINES_MARKERS,
                       name=radar) for radar in radar_names
        ],
        'layout': go.Layout(title=f"Comparison for {selected_stat}")

    }


@app.callback(Output('overview-content', 'children'), [Input('tabs', 'active_tab')])
def update_overview_figure(tab):
    if tab != 'tab-4':
        raise dash.exceptions.PreventUpdate

    conn = sqlite3.connect(DATA_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Radar_Name FROM biases")
    radars = [radar[0] for radar in cursor.fetchall()]

    radar_graphs = []
    for idx, radar in enumerate(radars):
        cursor.execute(
            "SELECT * FROM detection_rates WHERE ds_name=?", (radar,))
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


@app.callback(
    Output('download-report', 'data'),
    Input('generate-report-button', 'n_clicks'),
    State('date-range-picker', 'start_date'),
    State('date-range-picker', 'end_date')
)
def generate_report(n_clicks, start_date, end_date):
    if n_clicks is None:
        raise PreventUpdate

    # Fetch data from the database based on the date range
    conn_report = sqlite3.connect(DATA_DB)  # Use a different name here
    cursor = conn_report.cursor()
    cursor.execute('''
        SELECT * FROM detection_rates 
        WHERE Job_Date BETWEEN ? AND ?
    ''', (start_date, end_date))
    data = cursor.fetchall()
    conn.close()

    # Create PDF document
    buffer = io.BytesIO()  # Use an in-memory buffer
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Add title and other content
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Radar Statistics Report", styles['h1']))
    elements.append(Paragraph(f"Date Range: {start_date} to {
                    end_date}", styles['Normal']))
    elements.append(Spacer(1, 12))  # Add some space

    # Add table of data
    table_data = [cursor.description] + data
    table_data = [[Paragraph(str(cell), styles['Normal'])
                   for cell in row] for row in table_data]

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)

    ]))
    elements.append(table)

    doc.build(elements)
    # Return the PDF data for download
    buffer.seek(0)
    return dcc.send_bytes(buffer.getvalue(), 'radar_report.pdf')


if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
