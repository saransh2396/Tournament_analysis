import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

tabs = st.tabs(["Attack", "Style", "Pressing", "Low Block", "Possession Chains", "Rolling PPDA"])

def plot(metric, source_df=df):
    ascending = True if metric in LOWER_BETTER else False
    df_sorted = source_df.sort_values(metric, ascending=ascending)

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


# ─────────────────────────────────────────────────────────────────────────
# Helper: load one of the extra season-aggregate CSVs, cached in session
# ─────────────────────────────────────────────────────────────────────────
def load_extra_csv(session_key: str, label: str, uploader_key: str) -> pd.DataFrame | None:
    """Show a small uploader (only if not already loaded) and return the cleaned df."""
    if session_key not in st.session_state:
        file = st.file_uploader(f"Upload {label}", type=["csv"], key=uploader_key)
        if file is None:
            st.info(f"⬆️ Upload **{label}** to see this tab.")
            return None
        loaded = pd.read_csv(file)
        loaded = loaded.loc[:, ~loaded.columns.str.contains("^Unnamed")]
        st.session_state[session_key] = loaded

    data = st.session_state[session_key].copy()
    for c in data.columns:
        if c not in ("Team", "Block_Style", "window_label"):
            data[c] = pd.to_numeric(data[c], errors="coerce")
    return data


# ─────────────────────────────────────────────────────────────────────────
# TAB: Low Block Index
# ─────────────────────────────────────────────────────────────────────────
with tabs[3]:
    st.subheader("🧱 Low Block Index")
    lbi = load_extra_csv("lbi_df", "LowBlockIndex_La_Liga.csv", "lbi_uploader")

    if lbi is not None:
        LBI_METRICS_LOWER_BETTER = []  # none are "lower is better" for this set
        lbi_metrics = ["Low_Block_Index", "Avg_Def_Action_X", "Def_Actions_Def3rd_Pct",
                        "Def_Actions_Mid3rd_Pct", "Def_Actions_Att3rd_Pct", "Def_Actions_Own_Half_Pct"]
        lbi_metrics = [m for m in lbi_metrics if m in lbi.columns]

        c1, c2 = st.columns([2, 1])
        with c1:
            metric = st.selectbox("Metric", lbi_metrics, key="lbi_metric")
        with c2:
            if "Block_Style" in lbi.columns:
                styles = sorted(lbi["Block_Style"].dropna().unique().tolist())
                style_filter = st.multiselect("Filter Block Style", styles, default=styles)
                lbi = lbi[lbi["Block_Style"].isin(style_filter)]

        ascending = metric in LBI_METRICS_LOWER_BETTER
        lbi_sorted = lbi.sort_values(metric, ascending=ascending)

        fig = px.bar(
            lbi_sorted, x="Team", y=metric,
            color="Block_Style" if "Block_Style" in lbi_sorted.columns else None,
            category_orders={"Team": lbi_sorted["Team"].tolist()},
            title=metric,
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Full table"):
            st.dataframe(lbi_sorted, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────
# TAB: Possession Chains
# ─────────────────────────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("🔗 Possession Chains")
    pc = load_extra_csv("pc_df", "PossessionChains_La_Liga.csv", "pc_uploader")

    if pc is not None:
        chain_type = st.radio(
            "Chain type", ["Overall", "Counter_Attack", "Sustained_Buildup", "Transitional"],
            horizontal=True, key="pc_chain_type"
        )

        if chain_type == "Overall":
            pc_metrics = ["total_possessions", "avg_duration_s", "avg_chain_xT", "avg_xT_per_touch"]
        else:
            pc_metrics = [c for c in pc.columns if c.startswith(chain_type)]

        pc_metrics = [m for m in pc_metrics if m in pc.columns]
        metric = st.selectbox("Metric", pc_metrics, key="pc_metric")

        pc_sorted = pc.sort_values(metric, ascending=False)
        fig = px.bar(
            pc_sorted, x="Team", y=metric,
            category_orders={"Team": pc_sorted["Team"].tolist()},
            title=metric,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Style mix per team (rate columns), stacked bar - nice overview
        rate_cols = [c for c in ["Counter_Attack_rate_%", "Sustained_Buildup_rate_%", "Transitional_rate_%"]
                     if c in pc.columns]
        if rate_cols:
            st.markdown("**Possession style mix (share of chains)**")
            melt = pc.melt(id_vars="Team", value_vars=rate_cols,
                            var_name="Chain Type", value_name="Rate %")
            melt["Chain Type"] = melt["Chain Type"].str.replace("_rate_%", "", regex=False)
            order = pc.sort_values("Counter_Attack_rate_%", ascending=False)["Team"].tolist() \
                if "Counter_Attack_rate_%" in pc.columns else pc["Team"].tolist()
            fig2 = px.bar(
                melt, x="Team", y="Rate %", color="Chain Type", barmode="stack",
                category_orders={"Team": order},
            )
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("📋 Full table"):
            st.dataframe(pc.sort_values(metric, ascending=False), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────
# TAB: Rolling PPDA (within-match windows, per team)
# ─────────────────────────────────────────────────────────────────────────
with tabs[5]:
    st.subheader("⏱️ Rolling PPDA (15-minute windows)")
    rppda = load_extra_csv("rppda_df", "RollingPPDA_La_Liga.csv", "rppda_uploader")

    if rppda is not None:
        all_teams = sorted(rppda["Team"].unique().tolist())
        default_teams = all_teams[:5]
        selected_teams = st.multiselect("Teams to show", all_teams, default=default_teams, key="rppda_teams")

        if not selected_teams:
            st.info("Pick at least one team.")
        else:
            plot_df = rppda[rppda["Team"].isin(selected_teams)].sort_values("window_start_min")

            fig = go.Figure()
            for team in selected_teams:
                td = plot_df[plot_df["Team"] == team]
                fig.add_trace(go.Scatter(
                    x=td["window_label"], y=td["avg_PPDA_window"],
                    mode="lines+markers", name=team,
                ))

            fig.update_layout(
                title="Average PPDA by match window (lower = more intense press)",
                xaxis_title="Match window", yaxis_title="Avg PPDA",
                height=550,
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("📉 Lower PPDA = more passes allowed per defensive action = higher press intensity")

        with st.expander("📋 Full table"):
            st.dataframe(rppda, use_container_width=True)
