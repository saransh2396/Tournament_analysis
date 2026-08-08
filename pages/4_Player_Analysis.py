import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Player Analysis Dashboard")

# ─── Upload ───────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Upload Player CSV", type=["csv"])

if uploaded is None:
    st.stop()

df = pd.read_csv(uploaded)

# ─── Validation ───────────────────────────────────────────────────────────────
required_cols = ["Player", "Team", "Minutes"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing required column: {col}")
        st.stop()

# ─── Clean ────────────────────────────────────────────────────────────────────
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

# Convert numeric
for col in df.columns:
    if col not in ["Player", "Team"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ─── YOUR METRICS ─────────────────────────────────────────────────────────────
COLS = ["Shot_Att", "SOT", "Passes in final 3rd", "PPA","Progressive_Carries",
        "Prog_passes", "PrgR", "SCA", "GCA","xT","High_Turnovers","Assisted_Shots",
        "Interception_succ","Clearance_succ","Aerial_succ","BallTouch_succ",
        "BallRecovery_succ","Tackle_succ","TakeOn_succ","GCA_per_SCA",
        "SCA_per100Pass","GCA_per100Pass"]

COLS = [c for c in COLS if c in df.columns]

LOWER_BETTER = []  # none for now

# ─── Per90 Toggle ─────────────────────────────────────────────────────────────
per90 = st.toggle("Convert to Per90 Stats")

if per90:
    df_per90 = df.copy()
    for col in COLS:
        df_per90[col] = (df[col] / df["Minutes"]) * 90
    df = df_per90

# ─── Minutes Filter ───────────────────────────────────────────────────────────
min_minutes = st.slider(
    "Minimum Minutes Played",
    int(df["Minutes"].min()),
    int(df["Minutes"].max()),
    10
)

df = df[df["Minutes"] >= min_minutes]

# ─── Metric Selection ─────────────────────────────────────────────────────────
metric = st.selectbox("Select Metric", COLS)

ascending = True if metric in LOWER_BETTER else False

# ─── SECTION 1: PLAYER RANKINGS ───────────────────────────────────────────────
st.subheader("Player Rankings")

df_rank = df.sort_values(metric, ascending=ascending).reset_index(drop=True)
df_rank["Rank"] = df_rank[metric].rank(ascending=ascending, method="min")

st.dataframe(
    df_rank[["Rank", "Player", "Team", metric]],
    use_container_width=True
)

st.markdown("---")

# ─── SECTION 2: TEAM CONTRIBUTION ─────────────────────────────────────────────
st.subheader("Team Contribution")

team = st.selectbox("Select Team", df["Team"].unique())

df_team = df[df["Team"] == team].sort_values(metric, ascending=ascending)


fig_team = px.bar(
    df_team.head(10),
    x="Player",
    y=metric,
    text=metric,
    title=f"{team} - Top Contributors ({metric})"
)

fig_team.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig_team, use_container_width=True)

st.markdown("---")

# ─── SECTION 3: SCATTER ───────────────────────────────────────────────────────
st.subheader("Scatter Analysis")

col1, col2 = st.columns(2)

with col1:
    x_metric = st.selectbox("X-axis", COLS, key="x")

with col2:
    y_metric = st.selectbox("Y-axis", COLS, key="y")

# ─── Size based on Minutes per 90 ────────────────────────────────────────────
df["minutes_per90"] = df["Minutes"] / 90

# Normalize for better visuals (important)
df["size_metric"] = (df["minutes_per90"] - df["minutes_per90"].min()) + 0.5

fig_scatter = px.scatter(
    df,
    x=x_metric,
    y=y_metric,
    size="size_metric",
    size_max=40,
    hover_name="Player",
    hover_data=["Minutes"],
    color="Team",
    title=f"{x_metric} vs {y_metric}"
)

# Mean lines
fig_scatter.add_vline(x=df[x_metric].mean(), line_dash="dash",line_color="yellow")
fig_scatter.add_hline(y=df[y_metric].mean(), line_dash="dash",line_color="yellow")

st.plotly_chart(fig_scatter, use_container_width=True)