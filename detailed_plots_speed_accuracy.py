import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import numpy as np

# Load the transformed CSV file
fname = "./data_test/typewriting/865437_writing_keyboard_2025-03-07_15h19.54.006_export.csv"
df = pd.read_csv(fname)

# Convert to numeric
df["keypress_time_ms"] = pd.to_numeric(df["keypress_time"], errors="coerce") * 1000

# Filter data for only 'copy' task
df = df[df["task"] == "copy"]

# Group characters by trial number
word_id = 0
words_mapping = {}
separated_words = []
current_word = []
current_trial = -1
word_id_map = {}
total_chars = 0
total_time = 0

# Track words that contain at least one backspace
words_with_errors = set()

for i, row in df.iterrows():
    trial = row["trial"]
    # Clean the key string: remove leading/trailing spaces, make lowercase
    key_raw = str(row["key"]).strip().lower()
    keypress_time = row["keypress_time_ms"]

    # If we've moved to a new trial, finalize the previous one
    if trial != current_trial:
        if current_word:
            word_text = "".join(current_word)
            word_label = f"copy_{word_id}"
            words_mapping[word_label] = word_text
            separated_words.append((word_label, word_text))
            word_id += 1

        # Prepare for a new trial
        current_word = []
        current_trial = trial

    # If key is backspace, remove the last character from the current word
    if key_raw == "backspace":
        if current_word:
            current_word.pop()
        # Mark this word (which hasn't finished yet) as having an error
        words_with_errors.add(f"copy_{word_id}")
    elif key_raw not in ["space", "minus", "comma", "backspace"]:
        current_word.append(key_raw)
        total_chars += 1

    # Map each DataFrame row -> current word ID
    word_id_map[i] = f"copy_{word_id}"

    # Accumulate total time (for WPM calculations)
    if not pd.isna(keypress_time):
        total_time += keypress_time

# Finalize the last trial if needed
if current_word:
    word_text = "".join(current_word)
    word_label = f"copy_{word_id}"
    words_mapping[word_label] = word_text
    separated_words.append((word_label, word_text))

# Compute overall stats
num_words = len(separated_words)
typing_speed_wpm = (total_chars / 5) / (total_time / 60000) if total_time > 0 else 0

# A word is considered an error if it had a backspace
num_words_with_errors = len(words_with_errors)
overall_accuracy = (1 - num_words_with_errors / num_words) * 100 if num_words > 0 else 100

# Build a dictionary for per-word accuracy (100% or 0%)
word_accuracies = {}
for (wid, wtxt) in separated_words:
    if wid in words_with_errors:
        word_accuracies[wid] = 0
    else:
        word_accuracies[wid] = 100

# Update DataFrame with correct word_id mapping
df["word_id"] = df.index.map(word_id_map)

# Save separated words to a file
pd.DataFrame(separated_words, columns=["word_id", "word"]).to_csv("separated_words.csv", index=False)

# Dash App Setup
app = Dash(__name__)

app.layout = html.Div([
    html.H2("Typing Analysis Dashboard - Copy Task", style={"textAlign": "center"}),

    html.Div([
        html.P(f"Overall Typing Speed: {typing_speed_wpm:.2f} WPM"),
        html.P(f"Overall Accuracy: {overall_accuracy:.2f}%")
    ], style={"textAlign": "center", "marginBottom": "20px"}),

    dcc.Dropdown(
        id="word-dropdown",
        # Add "Overall" plus each word in the dropdown
        options=[{"label": "Overall", "value": "overall"}]
                + [{"label": f"{wid} -> {words_mapping[wid]} ({word_accuracies[wid]}%)",
                    "value": wid} for wid in words_mapping],
        placeholder="Select a word",
        style={"width": "50%", "margin": "auto"}
    ),

    html.Div([
        dcc.Graph(id="keypress-time-plot"),
        dcc.Graph(id="iki-plot")
    ], style={"width": "80%", "margin": "auto", "padding-top": "30px"})
])

@app.callback(
    [Output("keypress-time-plot", "figure"), Output("iki-plot", "figure")],
    [Input("word-dropdown", "value")]
)
def update_plots(word_id):
    if not word_id:
        return go.Figure(), go.Figure()

    # If user selects "Overall", return empty plots
    if word_id == "overall":
        return go.Figure(), go.Figure()

    # Otherwise, filter the DataFrame for that word_id
    filtered_df = df[df["word_id"] == word_id].copy()

    # If no rows, just empty
    if filtered_df.empty:
        return go.Figure(), go.Figure()

    # Sort by time for correct sequence
    filtered_df = filtered_df.sort_values(by="keypress_time_ms")

    # Compute IKI
    filtered_df["IKI_ms"] = filtered_df["keypress_time_ms"].diff()

    # 1) Keypress Time
    fig1 = go.Figure(go.Bar(
        x=filtered_df["key"],
        y=filtered_df["keypress_time_ms"],
        marker_color="#1f77b4",
        marker_line_width=1,
        marker_line_color="black"
    ))
    fig1.update_layout(
        title="Keypress Time per Letter",
        xaxis_title="Letter",
        yaxis_title="Time (ms)"
    )

    # 2) IKI Plot
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=filtered_df["key"].iloc[1:],
        y=filtered_df["IKI_ms"].iloc[1:],
        marker_color="#ff7f0e",
        marker_line_width=1,
        marker_line_color="black",
        name="IKI Bar"
    ))
    fig2.add_trace(go.Scatter(
        x=filtered_df["key"].iloc[1:],
        y=filtered_df["IKI_ms"].iloc[1:],
        mode="lines+markers",
        line=dict(color="red"),
        name="IKI Line"
    ))
    fig2.update_layout(
        title="Inter-Key Interval (IKI) per Letter",
        xaxis_title="Letter",
        yaxis_title="IKI (ms)"
    )

    return fig1, fig2


if __name__ == "__main__":
    app.run_server(debug=True)
