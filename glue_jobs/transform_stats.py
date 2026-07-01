"""
app.py
NBA Analytics Dashboard — Streamlit frontend
Reads processed data from AWS Athena via boto3.
Run locally: streamlit run dashboard/app.py
"""

import os
import time
import boto3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from io import StringIO
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NBA Analytics",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark court-inspired theme */
    .stApp { background-color: #0d1117; }
    section[data-testid="stSidebar"] { background-color: #161b22; }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
    }
    div[data-testid="metric-container"] label {
        color: #8b949e !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #f97316 !important;
        font-size: 1.8rem !important;
        font-weight: 700;
    }

    /* Section headers */
    .section-header {
        color: #f97316;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    /* Tab styling */
    button[data-baseweb="tab"] {
        color: #8b949e !important;
        font-weight: 500;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #f97316 !important;
        border-bottom-color: #f97316 !important;
    }

    /* Dataframe */
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Athena helpers ────────────────────────────────────────────────────────────
ATHENA_DATABASE      = os.getenv("ATHENA_DATABASE", "nba_analytics")
ATHENA_OUTPUT_BUCKET = os.getenv("ATHENA_OUTPUT_BUCKET", "s3://nba-analytics-camron/athena-results/")
AWS_REGION           = os.getenv("AWS_REGION", "us-east-1")
WORKGROUP            = "nba-analytics-workgroup"


@st.cache_data(ttl=3600)
def run_athena_query(sql: str) -> pd.DataFrame:
    """Execute a SQL query against Athena and return results as a DataFrame."""
    client = boto3.client("athena", region_name=AWS_REGION)

    response = client.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT_BUCKET},
        WorkGroup=WORKGROUP,
    )
    query_id = response["QueryExecutionId"]

    # Poll until complete
    for _ in range(60):
        status = client.get_query_execution(QueryExecutionId=query_id)
        state  = status["QueryExecution"]["Status"]["State"]
        if state == "SUCCEEDED":
            break
        elif state in ("FAILED", "CANCELLED"):
            reason = status["QueryExecution"]["Status"].get("StateChangeReason", "Unknown")
            st.error(f"Query failed: {reason}")
            return pd.DataFrame()
        time.sleep(2)

    # Fetch results
    paginator = client.get_paginator("get_query_results")
    rows, columns = [], []
    for page in paginator.paginate(QueryExecutionId=query_id):
        if not columns:
            columns = [c["Label"] for c in page["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
        for row in page["ResultSet"]["Rows"][1:]:
            rows.append([d.get("VarCharValue", "") for d in row["Data"]])

    return pd.DataFrame(rows, columns=columns)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏀 NBA Analytics")
    st.markdown("---")
    season = st.selectbox("Season", ["2024-25", "2023-24"], index=0)
    st.markdown("---")
    st.markdown('<p class="section-header">Navigation</p>', unsafe_allow_html=True)
    page = st.radio(
        "",
        ["Player Stats", "Team Standings", "Shot Analysis"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Data: NBA API → AWS S3 → Athena")
    st.caption("Refreshed daily at 6 AM UTC")


# ── Page: Player Stats ────────────────────────────────────────────────────────
if page == "Player Stats":
    st.markdown("# Player Performance")
    st.markdown('<p class="section-header">2024–25 Regular Season</p>', unsafe_allow_html=True)

    with st.spinner("Loading player data..."):
        df = run_athena_query(f"""
            SELECT player_name, team_abbreviation, games_played,
                   CAST(points_per_game AS DOUBLE)   AS ppg,
                   CAST(assists_per_game AS DOUBLE)  AS apg,
                   CAST(rebounds_per_game AS DOUBLE) AS rpg,
                   CAST(field_goal_pct AS DOUBLE)    AS fg_pct,
                   CAST(three_point_pct AS DOUBLE)   AS three_pct,
                   CAST(efficiency_rating AS DOUBLE) AS efficiency,
                   CAST(true_shooting_pct AS DOUBLE) AS ts_pct
            FROM nba_analytics.player_stats_9176f12ef772ee75d103ae33d34b608b
            WHERE season = '{season}' AND CAST(games_played AS INT) >= 20
            ORDER BY ppg DESC
            LIMIT 50
        """)

    if df.empty:
        st.warning("No data available. Make sure the pipeline has run and data is in S3.")
        st.stop()

    # Convert numeric columns
    for col in ["ppg", "apg", "rpg", "fg_pct", "three_pct", "efficiency", "ts_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── KPI row ───────────────────────────────────────────────────────────────
    top = df.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Scoring Leader",    top["player_name"],        f"{top['ppg']} PPG")
    col2.metric("Top Efficiency",    df.loc[df["efficiency"].idxmax(), "player_name"],
                                     f"{df['efficiency'].max():.1f} EFF")
    col3.metric("Best FG%",          df.loc[df["fg_pct"].idxmax(), "player_name"],
                                     f"{df['fg_pct'].max()*100:.1f}%")
    col4.metric("Best 3PT%",         df.loc[df["three_pct"].idxmax(), "player_name"],
                                     f"{df['three_pct'].max()*100:.1f}%")

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Top 15 Scorers")
        fig = px.bar(
            df.head(15),
            x="ppg", y="player_name",
            orientation="h",
            color="ppg",
            color_continuous_scale=["#1f2937", "#f97316"],
            labels={"ppg": "Points Per Game", "player_name": ""},
            text="ppg",
        )
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font_color="#e6edf3", coloraxis_showscale=False,
            yaxis={"categoryorder": "total ascending"},
            margin=dict(l=0, r=20, t=10, b=0), height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("#### Scoring vs Efficiency")
        fig2 = px.scatter(
            df,
            x="ppg", y="efficiency",
            size="games_played", color="apg",
            hover_name="player_name",
            hover_data={"ppg": ":.1f", "apg": ":.1f", "rpg": ":.1f"},
            color_continuous_scale=["#1f6feb", "#f97316"],
            labels={"ppg": "Points Per Game", "efficiency": "Efficiency Rating", "apg": "APG"},
        )
        fig2.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font_color="#e6edf3",
            margin=dict(l=0, r=0, t=10, b=0), height=420,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Full table ────────────────────────────────────────────────────────────
    st.markdown("#### Full Stats Table")
    display_df = df.copy()
    display_df["fg_pct"]    = (display_df["fg_pct"]    * 100).round(1).astype(str) + "%"
    display_df["three_pct"] = (display_df["three_pct"] * 100).round(1).astype(str) + "%"
    display_df["ts_pct"]    = (display_df["ts_pct"]    * 100).round(1).astype(str) + "%"
    display_df.columns      = ["Player", "Team", "GP", "PPG", "APG", "RPG", "FG%", "3PT%", "EFF", "TS%"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# ── Page: Team Standings ──────────────────────────────────────────────────────
elif page == "Team Standings":
    st.markdown("# Team Standings")
    st.markdown('<p class="section-header">2024–25 Regular Season</p>', unsafe_allow_html=True)

    with st.spinner("Loading standings..."):
        df = run_athena_query(f"""
            SELECT team_city || ' ' || team_name AS team,
                   team_abbreviation, conference, division,
                   CAST(wins AS INT)                       AS wins,
                   CAST(losses AS INT)                     AS losses,
                   CAST(win_pct AS DOUBLE)                 AS win_pct,
                   win_pct_label,
                   CAST(points_per_game AS DOUBLE)         AS ppg,
                   CAST(opp_points_per_game AS DOUBLE)     AS opp_ppg,
                   CAST(net_rating AS DOUBLE)              AS net_rating,
                   home_record, away_record, last_10_record
            FROM nba_analytics.team_standings_6ff06ce83ae7e28c21f653db1b53f120
            WHERE season = '{season}'
            ORDER BY win_pct DESC
        """)

    if df.empty:
        st.warning("No standings data available.")
        st.stop()

    for col in ["wins", "losses", "win_pct", "ppg", "opp_ppg", "net_rating"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── KPI row ───────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    best  = df.iloc[0]
    col1.metric("Best Record",    best["team"], f"{best['wins']}-{best['losses']}")
    col2.metric("Best Net Rating",df.loc[df["net_rating"].idxmax(), "team"],
                                  f"+{df['net_rating'].max():.1f}")
    col3.metric("Top Offense",    df.loc[df["ppg"].idxmax(), "team"],
                                  f"{df['ppg'].max():.1f} PPG")
    col4.metric("Top Defense",    df.loc[df["opp_ppg"].idxmin(), "team"],
                                  f"{df['opp_ppg'].min():.1f} Opp PPG")

    st.markdown("---")

    # ── Conference tabs ───────────────────────────────────────────────────────
    tab_east, tab_west = st.tabs(["Eastern Conference", "Western Conference"])

    for tab, conf in [(tab_east, "East"), (tab_west, "West")]:
        with tab:
            conf_df = df[df["conference"] == conf].reset_index(drop=True)
            conf_df.index += 1

            fig = px.bar(
                conf_df,
                x="team", y="net_rating",
                color="net_rating",
                color_continuous_scale=["#1f6feb", "#30363d", "#f97316"],
                labels={"net_rating": "Net Rating", "team": ""},
                text="net_rating",
            )
            fig.update_traces(texttemplate="%{text:+.1f}", textposition="outside")
            fig.update_layout(
                plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                font_color="#e6edf3", coloraxis_showscale=False,
                xaxis_tickangle=-30,
                margin=dict(l=0, r=0, t=10, b=0), height=350,
            )
            st.plotly_chart(fig, use_container_width=True)

            disp = conf_df[["team", "wins", "losses", "win_pct", "win_pct_label",
                            "ppg", "opp_ppg", "net_rating",
                            "home_record", "away_record", "last_10_record"]].copy()
            disp["win_pct"] = (disp["win_pct"] * 100).round(1).astype(str) + "%"
            disp.columns    = ["Team", "W", "L", "WIN%", "Tier",
                                "OFF PPG", "DEF PPG", "NET RTG",
                                "Home", "Away", "L10"]
            st.dataframe(disp, use_container_width=True)


# ── Page: Shot Analysis ───────────────────────────────────────────────────────
elif page == "Shot Analysis":
    st.markdown("# Shot Analysis")
    st.markdown('<p class="section-header">2024–25 Regular Season</p>', unsafe_allow_html=True)

    with st.spinner("Loading shot data..."):
        players_df = run_athena_query(f"""
            SELECT DISTINCT player_name
            FROM nba_analytics.shot_charts
            WHERE season = '{season}'
            ORDER BY player_name
        """)

    if players_df.empty:
        st.warning("No shot chart data available.")
        st.stop()

    selected_player = st.selectbox("Select Player", players_df["player_name"].tolist())

    with st.spinner(f"Loading shot data for {selected_player}..."):
        shots_df = run_athena_query(f"""
            SELECT shot_zone_label, shot_zone_basic, shot_zone_area,
                   CAST(loc_x AS INT)            AS loc_x,
                   CAST(loc_y AS INT)            AS loc_y,
                   CAST(shot_distance AS INT)    AS shot_distance,
                   CAST(shot_made_flag AS INT)   AS shot_made_flag,
                   made_label, action_type, shot_type,
                   CAST(period AS INT)           AS period,
                   CAST(minutes_remaining AS INT) AS minutes_remaining
            FROM nba_analytics.shot_charts
            WHERE season = '{season}' AND player_name = '{selected_player}'
        """)

    if shots_df.empty:
        st.warning(f"No shot data for {selected_player}.")
        st.stop()

    for col in ["loc_x", "loc_y", "shot_distance", "shot_made_flag", "period", "minutes_remaining"]:
        shots_df[col] = pd.to_numeric(shots_df[col], errors="coerce")

    total      = len(shots_df)
    makes      = shots_df["shot_made_flag"].sum()
    fg_pct     = makes / total * 100 if total else 0
    threes     = shots_df[shots_df["shot_type"] == "3PT Field Goal"]
    three_pct  = threes["shot_made_flag"].mean() * 100 if len(threes) else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Attempts", f"{total:,}")
    col2.metric("Field Goal %",   f"{fg_pct:.1f}%")
    col3.metric("3PT Attempts",   f"{len(threes):,}")
    col4.metric("3PT %",          f"{three_pct:.1f}%")

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Shot Chart")
        fig = px.scatter(
            shots_df,
            x="loc_x", y="loc_y",
            color="made_label",
            color_discrete_map={"Made": "#f97316", "Missed": "#30363d"},
            opacity=0.7,
            labels={"loc_x": "", "loc_y": "", "made_label": ""},
            title=f"{selected_player} — All Shot Locations",
        )
        fig.update_traces(marker=dict(size=5))
        # Draw basic court outline
        fig.add_shape(type="circle", x0=-75, y0=-75, x1=75, y1=75,
                      line=dict(color="#30363d", width=1))
        fig.add_shape(type="rect",   x0=-250, y0=-47.5, x1=250, y1=422.5,
                      line=dict(color="#30363d", width=1))
        fig.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font_color="#e6edf3",
            xaxis=dict(range=[-260, 260], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[-60, 440],  showgrid=False, zeroline=False, showticklabels=False),
            legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
            margin=dict(l=0, r=0, t=40, b=0), height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("#### FG% by Zone")
        zone_df = (
            shots_df.groupby("shot_zone_label")
            .agg(attempts=("shot_made_flag", "count"), makes=("shot_made_flag", "sum"))
            .reset_index()
        )
        zone_df["fg_pct"] = (zone_df["makes"] / zone_df["attempts"] * 100).round(1)

        fig2 = px.bar(
            zone_df.sort_values("fg_pct", ascending=True),
            x="fg_pct", y="shot_zone_label",
            orientation="h",
            color="fg_pct",
            color_continuous_scale=["#1f2937", "#f97316"],
            text="fg_pct",
            labels={"fg_pct": "FG%", "shot_zone_label": ""},
        )
        fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig2.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font_color="#e6edf3", coloraxis_showscale=False,
            margin=dict(l=0, r=20, t=10, b=0), height=420,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Clutch shots
    st.markdown("#### Clutch Shooting (Q4, ≤5 min remaining)")
    clutch = shots_df[(shots_df["period"] == 4) & (shots_df["minutes_remaining"] <= 5)]
    if len(clutch) > 0:
        clutch_pct = clutch["shot_made_flag"].mean() * 100
        st.markdown(f"**{len(clutch)} clutch attempts — {clutch_pct:.1f}% FG**")
        fig3 = px.scatter(
            clutch, x="loc_x", y="loc_y",
            color="made_label",
            color_discrete_map={"Made": "#f97316", "Missed": "#30363d"},
            opacity=0.8,
        )
        fig3.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font_color="#e6edf3",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            margin=dict(l=0, r=0, t=10, b=0), height=300,
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No clutch shot data available for this player.")