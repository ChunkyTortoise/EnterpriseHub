"""
Plotly Dash: Responsive Layout + Cross-Chart Zoom Sync Demo
-----------------------------------------------------------
Demonstrates both deliverables from the job posting:
1) Responsive DBC layout (desktop/tablet/mobile)
2) Synchronized zooming between separate figures with different Y-axes

Run: pip install dash dash-bootstrap-components && python dash_zoom_sync_demo.py
"""

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes",
        }
    ],
)

# --- Sample data: waveform + XY scatter (different Y-scales) ---
t = np.linspace(0, 10, 1000)
waveform = np.sin(2 * np.pi * 1.5 * t) + 0.3 * np.sin(2 * np.pi * 5 * t)
xy_y = np.cumsum(np.random.default_rng(42).normal(0, 0.5, 1000))


def make_waveform_fig():
    fig = go.Figure(go.Scatter(x=t, y=waveform, mode="lines", name="Signal"))
    fig.update_layout(
        title="Waveform (amplitude)",
        xaxis_title="Time (s)",
        yaxis_title="Amplitude",
        margin=dict(l=50, r=20, t=40, b=40),
        height=320,
        template="plotly_white",
    )
    return fig


def make_xy_fig():
    fig = go.Figure(
        go.Scatter(
            x=t,
            y=xy_y,
            mode="lines",
            name="Cumulative",
            line=dict(color="#e74c3c"),
        )
    )
    fig.update_layout(
        title="XY Plot (cumulative displacement)",
        xaxis_title="Time (s)",
        yaxis_title="Displacement",
        margin=dict(l=50, r=20, t=40, b=40),
        height=320,
        template="plotly_white",
    )
    return fig


def make_spectrum_fig():
    freqs = np.fft.rfftfreq(len(t), d=t[1] - t[0])
    spectrum = np.abs(np.fft.rfft(waveform))
    fig = go.Figure(go.Scatter(x=freqs[:100], y=spectrum[:100], mode="lines", name="FFT"))
    fig.update_layout(
        title="Frequency Spectrum",
        xaxis_title="Frequency (Hz)",
        yaxis_title="Magnitude",
        margin=dict(l=50, r=20, t=40, b=40),
        height=320,
        template="plotly_white",
    )
    return fig


# --- Responsive layout ---
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H3(
                    "Responsive Dashboard with Synchronized Zoom",
                    className="text-center my-3",
                ),
                xs=12,
            )
        ),
        dbc.Row(
            dbc.Col(
                dbc.Alert(
                    "Zoom on any time-domain chart — the other syncs automatically. "
                    "Double-click to reset. Resize your browser to test responsiveness.",
                    color="info",
                    className="mb-3",
                ),
                xs=12,
            )
        ),
        # Two time-domain charts: side-by-side on desktop, stacked on mobile
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        id="waveform",
                        figure=make_waveform_fig(),
                        config={"displayModeBar": False, "responsive": True},
                    ),
                    xs=12,
                    md=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        id="xy-plot",
                        figure=make_xy_fig(),
                        config={"displayModeBar": False, "responsive": True},
                    ),
                    xs=12,
                    md=6,
                ),
            ],
            className="mb-3",
        ),
        # Full-width spectrum (independent axis — no zoom sync)
        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    id="spectrum",
                    figure=make_spectrum_fig(),
                    config={"displayModeBar": False, "responsive": True},
                ),
                xs=12,
            )
        ),
    ],
    fluid=True,
)


# --- Bidirectional zoom sync between waveform and XY plot ---
@app.callback(
    Output("xy-plot", "figure"),
    Input("waveform", "relayoutData"),
    State("xy-plot", "figure"),
    prevent_initial_call=True,
)
def sync_waveform_to_xy(relayout_data, xy_fig):
    if relayout_data is None:
        raise PreventUpdate

    if "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
        xy_fig["layout"]["xaxis"]["range"] = [
            relayout_data["xaxis.range[0]"],
            relayout_data["xaxis.range[1]"],
        ]
        xy_fig["layout"]["xaxis"]["autorange"] = False
        # Y-axis rescales independently
        xy_fig["layout"]["yaxis"]["autorange"] = True
        return xy_fig

    if "xaxis.autorange" in relayout_data:
        xy_fig["layout"]["xaxis"]["autorange"] = True
        xy_fig["layout"]["yaxis"]["autorange"] = True
        return xy_fig

    raise PreventUpdate


@app.callback(
    Output("waveform", "figure"),
    Input("xy-plot", "relayoutData"),
    State("waveform", "figure"),
    prevent_initial_call=True,
)
def sync_xy_to_waveform(relayout_data, wave_fig):
    if relayout_data is None:
        raise PreventUpdate

    if "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
        wave_fig["layout"]["xaxis"]["range"] = [
            relayout_data["xaxis.range[0]"],
            relayout_data["xaxis.range[1]"],
        ]
        wave_fig["layout"]["xaxis"]["autorange"] = False
        wave_fig["layout"]["yaxis"]["autorange"] = True
        return wave_fig

    if "xaxis.autorange" in relayout_data:
        wave_fig["layout"]["xaxis"]["autorange"] = True
        wave_fig["layout"]["yaxis"]["autorange"] = True
        return wave_fig

    raise PreventUpdate


if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
