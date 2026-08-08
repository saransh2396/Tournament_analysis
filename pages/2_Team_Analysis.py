import streamlit as st
import pandas as pd
import plotly.express as px

st.title("⭐ Team Analysis")

# ─── Check data ───────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.warning("⚠️ Please upload data from Home page")
    st.stop()

df = st.session_state.df.copy()

# ─── Clean data ───────────────────────────────────────────────────────────────
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

for col in df.columns:
    if col != "Team":
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ─── Team selector ────────────────────────────────────────────────────────────
team = st.selectbox("Select Team", df["Team"])

# ─── Metric groups ────────────────────────────────────────────────────────────
ATTACK_COLS = ["Shot_Att", "SOT", "Passes in final 3rd", "PPA","Progressive_Carries",
               "Prog_passes", "PrgR", "SCA", "GCA"]

STYLE_COLS = ["Field_tilt_%", "xT",
              "Shot_Ending_Passing_Sequence", "Goal_Ending_Passing_Sequence",
              "Buildup_Play_Sequence"]

PRESS_COLS = ["High_Turnovers", "PPDA"]

LOWER_BETTER = ["PPDA"]

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tabs = st.tabs(["Attack", "Style", "Pressing"])

# ─── Plot Function ────────────────────────────────────────────────────────────
def plot(metric):

    if metric not in df.columns:
        return

    ascending = True if metric in LOWER_BETTER else False

    df_sorted = df.sort_values(metric, ascending=ascending).reset_index(drop=True)


    # df_sorted["Highlight"] = df_sorted["Team"].apply(
    #     lambda x: "Selected" if x == team else "Other"
    # )
    #
    # fig = px.bar(
    #     df_sorted,
    #     x="Team",
    #     y=metric,
    #     color="Highlight",
    #     color_discrete_map={
    #         "Selected": "red",
    #         "Other": "lightgray"
    #     },
    #     title=metric
    # )
    #
    # st.plotly_chart(fig, use_container_width=True)
    df_sorted["Highlight"] = df_sorted["Team"].apply(
        lambda x: "Selected" if x == team else "Other"
    )

    fig = px.bar(
        df_sorted,
        x="Team",
        y=metric,
        color="Highlight",
        category_orders={"Team": df_sorted["Team"].tolist()},
        color_discrete_map={
            "Selected": "red",
            "Other": "lightgray"
        }
    )

    st.plotly_chart(fig, use_container_width=True, key=f"{metric}_{team}")

    # ─── Rank ────────────────────────────────────────────────────────────────
    rank = df[metric].rank(ascending=ascending)[df["Team"] == team].values[0]
    value = df[df["Team"] == team][metric].values[0]

    col1, col2 = st.columns(2)
    col1.metric("Value", round(value, 2))
    col2.metric("Rank", int(rank))

    # ─── Context ─────────────────────────────────────────────────────────────
    if metric in LOWER_BETTER:
        st.caption("📉 Lower values are better")
    else:
        st.caption("📈 Higher values are better")


# ─── ATTACK TAB ───────────────────────────────────────────────────────────────
with tabs[0]:
    st.subheader("⚔️ Attack")
    for m in ATTACK_COLS:
        plot(m)

# ─── STYLE TAB (NEWLY ADDED) ──────────────────────────────────────────────────
with tabs[1]:
    st.subheader("🧠 Style")
    for m in STYLE_COLS:
        plot(m)

# ─── PRESSING TAB ─────────────────────────────────────────────────────────────
with tabs[2]:
    st.subheader("🔥 Pressing")
    for m in PRESS_COLS:
        plot(m)