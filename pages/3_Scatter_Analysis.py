import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📊 Scatter Analysis")

# ─── Check data ───────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.warning("⚠️ Please upload data from Home page")
    st.stop()

df = st.session_state.df.copy()

# Clean
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

# Convert numeric
for col in df.columns:
    if col != "Team":
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ─── Metric groups ────────────────────────────────────────────────────────────
ATTACK_COLS = ["Shot_Att", "SOT", "Passes in final 3rd", "PPA","Progressive_Carries",
               "Prog_passes", "PrgR", "SCA", "GCA"]

STYLE_COLS = ["Field_tilt_%", "xT",
              "Shot_Ending_Passing_Sequence", "Goal_Ending_Passing_Sequence",
              "Buildup_Play_Sequence"]

PRESS_COLS = ["High_Turnovers", "PPDA"]

ALL_METRICS = ATTACK_COLS + STYLE_COLS + PRESS_COLS

# ─── Team highlight option ────────────────────────────────────────────────────
team = st.selectbox("Highlight Team (optional)", ["None"] + list(df["Team"]))

# ─── Axis selection ───────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    x_metric = st.selectbox("X-axis", ALL_METRICS)

with col2:
    y_metric = st.selectbox("Y-axis", ALL_METRICS)

# ─── Highlight logic ──────────────────────────────────────────────────────────
if team != "None":
    df["Highlight"] = df["Team"].apply(
        lambda x: "Selected" if x == team else "Other"
    )
else:
    df["Highlight"] = "All Teams"

# ─── Plot ─────────────────────────────────────────────────────────────────────
fig = px.scatter(
    df,
    x=x_metric,
    y=y_metric,
    color="Highlight",
    text="Team",
    color_discrete_map={
        "Selected": "red",
        "Other": "lightgray",
        "All Teams": "blue"
    },
    title=f"{x_metric} vs {y_metric}"
)

# ─── Mean lines (quadrants) ───────────────────────────────────────────────────
fig.add_vline(x=df[x_metric].mean(), line_dash="dash",line_color="yellow")
fig.add_hline(y=df[y_metric].mean(), line_dash="dash",line_color="yellow")


fig.update_traces(textposition="top center")

st.plotly_chart(fig, use_container_width=True)