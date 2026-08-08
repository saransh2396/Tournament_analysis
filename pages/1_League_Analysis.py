import streamlit as st
import pandas as pd
import plotly.express as px

st.title("League Analysis")

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

# Metric groups
ATTACK_COLS = ["Shot_Att", "SOT", "Passes in final 3rd", "PPA","Progressive_Carries",
               "Prog_passes", "PrgR", "SCA", "GCA"]

STYLE_COLS = ["Field_tilt_%", "xT",
              "Shot_Ending_Passing_Sequence", "Goal_Ending_Passing_Sequence",
              "Buildup_Play_Sequence"]

PRESS_COLS = ["High_Turnovers", "PPDA"]

LOWER_BETTER = ["PPDA"]

tabs = st.tabs(["Attack", "Style", "Pressing"])

def plot(metric):
    ascending = True if metric in LOWER_BETTER else False
    df_sorted = df.sort_values(metric, ascending=ascending)

    fig = px.bar(
        df_sorted,
        x="Team",
        y=metric,
        category_orders={"Team": df_sorted["Team"].tolist()},
        title=metric
    )

    st.plotly_chart(fig, use_container_width=True)

with tabs[0]:
    for m in ATTACK_COLS:
        if m in df.columns:
            plot(m)

with tabs[1]:
    for m in STYLE_COLS:
        if m in df.columns:
            plot(m)

with tabs[2]:
    for m in PRESS_COLS:
        if m in df.columns:
            plot(m)