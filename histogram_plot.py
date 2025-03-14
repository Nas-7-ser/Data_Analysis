import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# Load and Prepare Data
fname = "./data_test/typewriting/865437_writing_keyboard_2025-03-07_15h19.54.006_export.csv"
df = pd.read_csv(fname)

# Convert columns to numeric
df['keypress_duration'] = pd.to_numeric(df['keypress_duration'], errors='coerce')
df['keypress_time'] = pd.to_numeric(df['keypress_time'], errors='coerce')

# Convert seconds to milliseconds
df['keypress_duration_ms'] = df['keypress_duration'] * 1000
df['keypress_time_ms'] = df['keypress_time'] * 1000

# Calculate IKI (Inter-Key Interval)
df['IKI_ms'] = df.groupby(['task', 'trial'])['keypress_time_ms'].diff()

# Separate DataFrame for IKI (without NaNs)
df_iki = df.dropna(subset=['IKI_ms']).copy()

# Create the Dash Application
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Keyboard Duration & IKI Histograms", style={'textAlign': 'center'}),
    
    # Sliders for controlling the number of bins
    html.Div([
        html.Label("Keypress Duration Bins:"),
        dcc.Slider(
            id='duration-bins-slider',
            min=10,
            max=200,
            step=5,
            value=50,  # default
            marks={n: str(n) for n in range(10, 201, 20)}  # some intermediate labels
        ),
        html.Br(),
        html.Label("Inter-Key Interval (IKI) Bins:"),
        dcc.Slider(
            id='iki-bins-slider',
            min=10,
            max=200,
            step=5,
            value=50,  # default
            marks={n: str(n) for n in range(10, 201, 20)}
        )
    ], style={'width': '80%', 'margin': 'auto', 'padding': '20px'}),
    
    # Divs to hold the histogram figures
    html.Div([
        dcc.Graph(id='duration-hist'),
        dcc.Graph(id='iki-hist')
    ], style={'width': '80%', 'margin': 'auto'})
])

@app.callback(
    Output('duration-hist', 'figure'),
    Output('iki-hist', 'figure'),
    Input('duration-bins-slider', 'value'),
    Input('iki-bins-slider', 'value')
)
def update_histograms(duration_bins, iki_bins):
    # Build the Keypress Duration Histogram with the chosen nbins
    fig_duration = px.histogram(
        df,
        x='keypress_duration_ms',
        nbins=duration_bins,
        title='Keypress Duration Histogram (ms)',
        color_discrete_sequence=['#1f77b4']
    )
    fig_duration.update_traces(marker_line_color='black', marker_line_width=1)
    fig_duration.update_layout(
        xaxis_title='Duration (ms)',
        yaxis_title='Frequency'
    )
    
    # Build the IKI Histogram with the chosen nbins
    fig_iki = px.histogram(
        df_iki,
        x='IKI_ms',
        nbins=iki_bins,
        title='Inter-Key Interval (IKI) Histogram (ms)',
        color_discrete_sequence=['#ff7f0e']
    )
    fig_iki.update_traces(marker_line_color='black', marker_line_width=1)
    fig_iki.update_layout(
        xaxis_title='IKI (ms)',
        yaxis_title='Frequency'
    )
    
    return fig_duration, fig_iki

if __name__ == "__main__":
    app.run_server(debug=True)
