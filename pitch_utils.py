"""
Shared helper to draw an Opta-style football pitch (0-100 x 0-100 coords)
as Plotly shapes, so any page can drop a pitch under scatter/line traces.

Usage:
    fig = go.Figure()
    for shape in pitch_shapes():
        fig.add_shape(shape)
    fig.update_xaxes(range=[-2, 102], visible=False)
    fig.update_yaxes(range=[-2, 102], visible=False, scaleanchor="x")
"""

PITCH_LINE_COLOR = "rgba(255,255,255,0.35)"


def pitch_shapes(line_color: str = PITCH_LINE_COLOR, line_width: float = 1.5):
    """Return a list of Plotly shape dicts drawing a pitch on a 0-100 x 0-100 grid."""
    shapes = []

    def rect(x0, y0, x1, y1):
        shapes.append(dict(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                            line=dict(color=line_color, width=line_width),
                            fillcolor="rgba(0,0,0,0)", layer="below"))

    def line(x0, y0, x1, y1):
        shapes.append(dict(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                            line=dict(color=line_color, width=line_width),
                            layer="below"))

    def circle(cx, cy, r):
        shapes.append(dict(type="circle", x0=cx - r, y0=cy - r, x1=cx + r, y1=cy + r,
                            line=dict(color=line_color, width=line_width),
                            fillcolor="rgba(0,0,0,0)", layer="below"))

    # Outer boundary
    rect(0, 0, 100, 100)
    # Halfway line
    line(50, 0, 50, 100)
    # Centre circle + spot
    circle(50, 50, 9.15)
    circle(50, 50, 0.4)

    # Penalty boxes (18-yard) - Opta: 100 units long pitch, 100 wide
    # Left box
    rect(0, 21.1, 17.0, 78.9)
    # Left six-yard box
    rect(0, 36.8, 5.8, 63.2)
    # Left penalty spot
    circle(11.5, 50, 0.4)
    # Right box
    rect(83.0, 21.1, 100, 78.9)
    # Right six-yard box
    rect(94.2, 36.8, 100, 63.2)
    # Right penalty spot
    circle(88.5, 50, 0.4)

    # Goals (small rectangles poking outside the pitch)
    rect(-2, 44.2, 0, 55.8)
    rect(100, 44.2, 102, 55.8)

    return shapes


def empty_pitch_figure(title: str = "", bg_color: str = "#0A0E1A", height: int = 650):
    """Return a go.Figure pre-populated with a pitch, dark theme, correct aspect ratio."""
    import plotly.graph_objects as go

    fig = go.Figure()
    for shp in pitch_shapes():
        fig.add_shape(shp)

    fig.update_xaxes(range=[-3, 103], visible=False, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-3, 103], visible=False, showgrid=False, zeroline=False,
                      scaleanchor="x", scaleratio=1)
    fig.update_layout(
        title=title,
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        font=dict(color="#E6E6E6"),
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig
