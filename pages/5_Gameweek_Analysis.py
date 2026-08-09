import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pitch_utils import empty_pitch_figure

st.set_page_config(layout="wide")
st.title("📅 Gameweek Analysis")
st.caption("Match-by-match trends and per-match passing / defensive networks, built from the raw event data.")

# ─────────────────────────────────────────────────────────────────────────
# Load event data (cached, expensive to parse — ~500k+ rows)
# ─────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading event data...")
def load_events(file) -> pd.DataFrame:
    df = pd.read_parquet(file)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    return df


@st.cache_data(show_spinner="Building match-level summary...")
def build_match_summary(events: pd.DataFrame) -> pd.DataFrame:
    """One row per (game_id, team): match number for that team, opponent, and headline metrics."""

    def agg(g: pd.DataFrame) -> pd.Series:
        passes = g[g["type"] == "Pass"]
        completed = (passes["outcomeType"] == "Successful").sum()
        attempted = len(passes)
        return pd.Series({
            "Field_Tilt_%": g["Field_Tilt_%"].iloc[0] if "Field_Tilt_%" in g else None,
            "PPDA": g["PPDA"].iloc[0] if "PPDA" in g else None,
            "Shots": g["is_shot"].sum() if "is_shot" in g else None,
            "Goals": (g["type"] == "Goal").sum(),
            "High_Turnovers": g["high_turnovers"].sum() if "high_turnovers" in g else None,
            "Passes_Attempted": attempted,
            "Passes_Completed": completed,
            "Pass_Accuracy_%": round(100 * completed / attempted, 2) if attempted else 0,
            "Shot_Ending_Sequences": g["Shot_ending_passing_sequence"].sum()
                if "Shot_ending_passing_sequence" in g else None,
            "Goal_Ending_Sequences": g["Goal_ending_passing_sequence"].sum()
                if "Goal_ending_passing_sequence" in g else None,
        })

    summary = events.groupby(["game_id", "game", "team"], as_index=False).apply(agg)

    # opponent + home/away
    opp_venue = summary.apply(
        lambda r: pd.Series({
            "Opponent": r["game"].split(" vs ")[1] if r["team"] == r["game"].split(" vs ")[0]
                        else r["game"].split(" vs ")[0],
            "Venue": "H" if r["team"] == r["game"].split(" vs ")[0] else "A",
        }), axis=1
    )
    summary = pd.concat([summary, opp_venue], axis=1)

    # chronological match number per team, using game_id order as the timeline
    summary = summary.sort_values(["team", "game_id"])
    summary["Match_No"] = summary.groupby("team").cumcount() + 1

    return summary.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def starting_xi_for(events: pd.DataFrame, game_id: float, team: str) -> list:
    m = events[(events["game_id"] == game_id) & (events["team"] == team)]
    subs_on = set(m.loc[m["type"] == "SubstitutionOn", "playerName"])
    return [p for p in m["playerName"].dropna().unique() if p not in subs_on]


@st.cache_data(show_spinner="Building passing network...")
def passing_network(events: pd.DataFrame, game_id: float, team: str):
    m = events[(events["game_id"] == game_id) & (events["team"] == team)] \
        .sort_values(["periodId", "minute", "second"]).reset_index(drop=True)

    xi = starting_xi_for(events, game_id, team)
    m_xi = m[m["playerName"].isin(xi)]

    avg_pos = m_xi.groupby("playerName")[["x", "y"]].mean()
    touches = m_xi.groupby("playerName").size().rename("touches")
    nodes = avg_pos.join(touches)

    edges = {}
    for i in range(len(m) - 1):
        row, nxt = m.iloc[i], m.iloc[i + 1]
        if (row["type"] == "Pass" and row["outcomeType"] == "Successful"
                and row["playerName"] in xi and nxt["playerName"] in xi
                and nxt["periodId"] == row["periodId"] and nxt["playerName"] != row["playerName"]):
            key = tuple(sorted([row["playerName"], nxt["playerName"]]))
            edges[key] = edges.get(key, 0) + 1

    return nodes, edges


@st.cache_data(show_spinner="Building defensive network...")
def defensive_network(events: pd.DataFrame, game_id: float, team: str):
    """Same shape as passing_network: nodes = avg position + action count per player,
    edges = how often two players made consecutive defensive actions (team's defensive
    sequence), which traces out the shape/connectivity of the block rather than just
    scattering raw event dots."""
    def_types = ["Tackle", "Interception", "Clearance", "Aerial", "BallRecovery"]

    m = events[(events["game_id"] == game_id) & (events["team"] == team)] \
        .sort_values(["periodId", "minute", "second"]).reset_index(drop=True)

    xi = starting_xi_for(events, game_id, team)

    dm = m[m["type"].isin(def_types)].reset_index(drop=True)
    dm_xi = dm[dm["playerName"].isin(xi)]

    avg_pos = dm_xi.groupby("playerName")[["x", "y"]].mean()
    n_actions = dm_xi.groupby("playerName").size().rename("n_actions")
    dominant_type = dm_xi.groupby("playerName")["type"].agg(lambda s: s.value_counts().idxmax()).rename("main_type")
    nodes = avg_pos.join(n_actions).join(dominant_type)

    edges = {}
    for i in range(len(dm_xi) - 1):
        row, nxt = dm_xi.iloc[i], dm_xi.iloc[i + 1]
        if row["playerName"] != nxt["playerName"]:
            key = tuple(sorted([row["playerName"], nxt["playerName"]]))
            edges[key] = edges.get(key, 0) + 1

    return nodes, edges


# ─────────────────────────────────────────────────────────────────────────
# UI: load file
# ─────────────────────────────────────────────────────────────────────────
if "events_df" not in st.session_state:
    up = st.file_uploader("Upload event-level data (Events_La_Liga.parquet)", type=["parquet"])
    if up is None:
        st.info("⬆️ Upload the events parquet file to unlock gameweek analysis.")
        st.stop()
    st.session_state.events_df = load_events(up)

events = st.session_state.events_df
summary = build_match_summary(events)

teams = sorted(summary["team"].unique().tolist())
team = st.selectbox("Team", teams)

team_summary = summary[summary["team"] == team].sort_values("Match_No")

# ─────────────────────────────────────────────────────────────────────────
# SECTION 1: Match-by-match trend line
# ─────────────────────────────────────────────────────────────────────────
st.subheader(f"📈 {team} — Match-by-match trend")

TREND_METRICS = ["Field_Tilt_%", "PPDA", "Shots", "Goals", "High_Turnovers",
                  "Passes_Completed", "Pass_Accuracy_%", "Shot_Ending_Sequences", "Goal_Ending_Sequences"]
TREND_METRICS = [m for m in TREND_METRICS if m in team_summary.columns]

metric = st.selectbox("Metric", TREND_METRICS)

hover = team_summary.apply(lambda r: f"{r['Opponent']} ({r['Venue']})", axis=1)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=team_summary["Match_No"], y=team_summary[metric],
    mode="lines+markers",
    text=hover, hovertemplate="MD %{x} vs %{text}<br>" + metric + ": %{y}<extra></extra>",
    line=dict(width=2),
))
fig.add_hline(y=team_summary[metric].mean(), line_dash="dash", line_color="yellow",
              annotation_text="Season avg", annotation_position="top left")
fig.update_layout(
    title=f"{metric} across the season",
    xaxis_title="Match number (chronological)",
    yaxis_title=metric,
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("📋 Match-by-match table"):
    st.dataframe(
        team_summary[["Match_No", "Opponent", "Venue"] + TREND_METRICS],
        use_container_width=True, hide_index=True,
    )

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────
# SECTION 2: Pick a match → Passing Network + Defensive Map side by side
# ─────────────────────────────────────────────────────────────────────────
st.subheader("🕸️ Passing Network & Defensive Network — single match")

match_options = team_summary.apply(
    lambda r: f"MD {int(r['Match_No'])}: vs {r['Opponent']} ({r['Venue']})", axis=1
).tolist()
match_lookup = dict(zip(match_options, team_summary["game_id"].tolist()))

chosen_match_label = st.selectbox("Select match", match_options, index=len(match_options) - 1)
chosen_game_id = match_lookup[chosen_match_label]

col1, col2 = st.columns(2)

# ── Passing network ────────────────────────────────────────────────────
with col1:
    nodes, edges = passing_network(events, chosen_game_id, team)

    pfig = empty_pitch_figure(title=f"Passing Network — {chosen_match_label}")

    if edges:
        max_w = max(edges.values())
        for (p1, p2), count in edges.items():
            if p1 not in nodes.index or p2 not in nodes.index:
                continue
            x1, y1 = nodes.loc[p1, ["x", "y"]]
            x2, y2 = nodes.loc[p2, ["x", "y"]]
            pfig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1, y2], mode="lines",
                line=dict(width=1 + 6 * (count / max_w), color="rgba(0,212,255,0.45)"),
                hoverinfo="skip", showlegend=False,
            ))

    if not nodes.empty:
        pfig.add_trace(go.Scatter(
            x=nodes["x"], y=nodes["y"], mode="markers+text",
            marker=dict(size=nodes["touches"] / nodes["touches"].max() * 35 + 15,
                        color="#FF4F9A", line=dict(width=1.5, color="white")),
            text=[n.split()[-1] for n in nodes.index],  # last name for label
            textposition="top center", textfont=dict(color="white", size=10),
            customdata=nodes.index, hovertemplate="%{customdata}<extra></extra>",
            showlegend=False,
        ))
    else:
        pfig.add_annotation(text="No passing data for this match", showarrow=False,
                             x=50, y=50, font=dict(color="white"))

    st.plotly_chart(pfig, use_container_width=True)
    st.caption("Node size = touches · Line width = pass frequency between the pair · Starting XI only")

# ── Defensive network ───────────────────────────────────────────────────
with col2:
    dnodes, dedges = defensive_network(events, chosen_game_id, team)

    dfig = empty_pitch_figure(title=f"Defensive Network — {chosen_match_label}")

    if dedges:
        max_w = max(dedges.values())
        for (p1, p2), count in dedges.items():
            if p1 not in dnodes.index or p2 not in dnodes.index:
                continue
            x1, y1 = dnodes.loc[p1, ["x", "y"]]
            x2, y2 = dnodes.loc[p2, ["x", "y"]]
            dfig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1, y2], mode="lines",
                line=dict(width=1 + 6 * (count / max_w), color="rgba(255,209,102,0.45)"),
                hoverinfo="skip", showlegend=False,
            ))

    if not dnodes.empty:
        type_color_map = {
            "Tackle": "#00D4FF", "Interception": "#FFD166", "Clearance": "#FF4F9A",
            "Aerial": "#7CFC00", "BallRecovery": "#B08CFF",
        }
        node_colors = dnodes["main_type"].map(type_color_map).fillna("#CCCCCC")
        dfig.add_trace(go.Scatter(
            x=dnodes["x"], y=dnodes["y"], mode="markers+text",
            marker=dict(size=dnodes["n_actions"] / dnodes["n_actions"].max() * 35 + 15,
                        color=node_colors, line=dict(width=1.5, color="white")),
            text=[n.split()[-1] for n in dnodes.index],  # last name for label
            textposition="top center", textfont=dict(color="white", size=10),
            customdata=list(zip(dnodes.index, dnodes["n_actions"], dnodes["main_type"])),
            hovertemplate="%{customdata[0]}<br>%{customdata[1]} actions · mostly %{customdata[2]}<extra></extra>",
            showlegend=False,
        ))
    else:
        dfig.add_annotation(text="No defensive events for this match", showarrow=False,
                             x=50, y=50, font=dict(color="white"))

    st.plotly_chart(dfig, use_container_width=True)
    st.caption("Node size = defensive actions · Node color = player's most common action type · "
               "Line width = how often the pair made consecutive defensive actions · Starting XI only")