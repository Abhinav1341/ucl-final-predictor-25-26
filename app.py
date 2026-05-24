import pandas as pd
import streamlit as st

from src.predict import predict_match

st.set_page_config(
    page_title="UCL Predictor",
    page_icon="🏆",
    layout="wide",
)

TEAM_LOGOS = {
    "Arsenal": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
    "PSG": "https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg",
    "Real Madrid": "https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg",
    "Manchester City": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
}
DEFAULT_LOGO = "https://upload.wikimedia.org/wikipedia/commons/1/1b/Square_200x200.png" # Fallback

st.title("🏆 UCL Match Predictor")
st.markdown("Predict outcomes, expected goals, and player performances for the UEFA Champions League.")

team_options = ["Arsenal", "PSG"]
formation_options = ["4-3-3", "4-2-3-1", "4-4-2", "3-4-3"]

st.divider()
header_col1, header_col2, header_col3 = st.columns([2, 1, 2], gap="large")

with header_col1:
    team_a = st.selectbox("Home Team", team_options, index=0)
    st.image(TEAM_LOGOS.get(team_a, DEFAULT_LOGO), width=100)
    team_a_formation = st.selectbox(
        f"{team_a} Formation",
        formation_options,
        index=0,
        key="team_a_formation",
    )

with header_col2:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>VS</h1>", unsafe_allow_html=True)

with header_col3:
    team_b = st.selectbox("Away Team", team_options, index=1)
    st.image(TEAM_LOGOS.get(team_b, DEFAULT_LOGO), width=100)
    team_b_formation = st.selectbox(
        f"{team_b} Formation",
        formation_options,
        index=0,
        key="team_b_formation",
    )

if team_a == team_b:
    st.warning("⚠️ Please choose two different teams to run the prediction.")
    st.stop()

with st.spinner('Calculating match probabilities...'):
    prediction = predict_match(
        team_a,
        team_b,
        team_a_formation=team_a_formation,
        team_b_formation=team_b_formation,
    )

st.divider()

tab_overview, tab_players, tab_lineups, tab_data = st.tabs([
    "📊 Match Overview", 
    "🎯 Player Projections", 
    "👕 Lineups", 
    "📈 Team & History Data"
])

with tab_overview:
    st.subheader("Match Outcome (90 Mins)")
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric(f"{team_a} Win", f"{prediction['team_a_win']:.1%}")
    metric_2.metric("Draw", f"{prediction['draw']:.1%}")
    metric_3.metric(f"{team_b} Win", f"{prediction['team_b_win']:.1%}")

    st.divider()
    
    xg_1, xg_2 = st.columns(2)
    with xg_1:
        st.subheader(f"{team_a} Expected Goals (xG)")
        st.metric("xG", prediction["team_a_xg"], help="Expected goals based on team strength and lineup")
        st.caption(f"Lineup modifier: {prediction['team_a_lineup_modifier']:.3f}x")
    with xg_2:
        st.subheader(f"{team_b} Expected Goals (xG)")
        st.metric("xG", prediction["team_b_xg"], help="Expected goals based on team strength and lineup")
        st.caption(f"Lineup modifier: {prediction['team_b_lineup_modifier']:.3f}x")

    st.divider()

    col_path, col_scores = st.columns(2)
    with col_path:
        st.subheader("Trophy Winner Path")
        path_rows = [
            {"Path": f"{team_a} win in 90", "Probability": f"{prediction['team_a_win']:.1%}"},
            {"Path": f"{team_b} win in 90", "Probability": f"{prediction['team_b_win']:.1%}"},
            {"Path": f"{team_a} win in extra time", "Probability": f"{prediction['team_a_extra_time_win']:.1%}"},
            {"Path": f"{team_b} win in extra time", "Probability": f"{prediction['team_b_extra_time_win']:.1%}"},
            {"Path": f"{team_a} win on penalties", "Probability": f"{prediction['team_a_penalty_win']:.1%}"},
            {"Path": f"{team_b} win on penalties", "Probability": f"{prediction['team_b_penalty_win']:.1%}"},
        ]
        st.dataframe(pd.DataFrame(path_rows), hide_index=True, use_container_width=True)

    with col_scores:
        st.subheader("Most Likely Scorelines")
        scoreline_rows = [
            {
                "Scoreline": f"{team_a} {sl['team_a_goals']} - {sl['team_b_goals']} {team_b}",
                "Probability": f"{sl['probability']:.1%}"
            } for sl in prediction["top_scorelines"]
        ]
        st.dataframe(pd.DataFrame(scoreline_rows), hide_index=True, use_container_width=True)

with tab_players:
    st.subheader("Likely Goalscorers")
    scorer_rows = [
        {
            "Player": s["player"], "Team": s["team"], "Position": s["position"],
            "xG": round(s["player_xg"], 2), "Goal Prob": f"{s['goal_probability']:.1%}",
            "Start Chance": f"{s['starting_probability']:.0%}", "Why": s["scorer_reason"]
        } for s in prediction["scorers"]
    ]
    st.dataframe(pd.DataFrame(scorer_rows).head(10), hide_index=True, use_container_width=True)

    st.subheader("Likely Assisters")
    assist_rows = [
        {
            "Player": a["player"], "Team": a["team"], "Position": a["position"],
            "xA": round(a["player_xa"], 2), "Assist Prob": f"{a['assist_probability']:.1%}",
            "Start Chance": f"{a['starting_probability']:.0%}", "Why": a["assist_reason"]
        } for a in prediction["assisters"]
    ]
    st.dataframe(pd.DataFrame(assist_rows).head(10), hide_index=True, use_container_width=True)

def squad_dataframe(rows):
    return pd.DataFrame([
        {
            "Player": row["player"], "Pos": row["position"], "Role": row.get("assigned_role", row["position"]),
            "Mins": row["expected_minutes"], "Start %": f"{row['starting_probability']:.0%}",
            "UCL G/A": f"{row['ucl_goals']} / {row['ucl_assists']}"
        } for row in rows
    ])

with tab_lineups:
    xi_1, xi_2 = st.columns(2)
    with xi_1:
        st.subheader(f"{team_a} XI")
        st.caption(f"Formation: {prediction['team_a_squad']['formation']}")
        st.dataframe(squad_dataframe(prediction["team_a_squad"]["likely_xi"]), hide_index=True, use_container_width=True)
        with st.expander("Show Substitutes"):
            st.dataframe(squad_dataframe(prediction["team_a_squad"]["substitutes"]), hide_index=True, use_container_width=True)

    with xi_2:
        st.subheader(f"{team_b} XI")
        st.caption(f"Formation: {prediction['team_b_squad']['formation']}")
        st.dataframe(squad_dataframe(prediction["team_b_squad"]["likely_xi"]), hide_index=True, use_container_width=True)
        with st.expander("Show Substitutes"):
            st.dataframe(squad_dataframe(prediction["team_b_squad"]["substitutes"]), hide_index=True, use_container_width=True)

with tab_data:
    st.subheader("Team Data Snapshot")
    team_stats_df = pd.DataFrame(prediction["team_stats"])
    display_cols = ["team", "matches", "goals_for_per_match", "goals_against_per_match", "xg_proxy_for_per_match", "possession"]
    st.dataframe(team_stats_df[display_cols].round(2), hide_index=True, use_container_width=True)

    st.subheader("Knockout Stage History")
    knockout_df = pd.DataFrame(prediction["knockout_matches"])
    knockout_df["date"] = pd.to_datetime(knockout_df["date"]).dt.strftime("%Y-%m-%d")
    st.dataframe(knockout_df[["date", "stage", "home_team", "away_team", "score"]], hide_index=True, use_container_width=True)

st.divider()
with st.expander("ℹ️ About this Model"):
    st.write(f"""
    This version uses your Excel workbooks as the primary data source. Team strength is derived from UCL league-stage goals, possession, shots, shots on target, and a simple xG proxy. 
    It also includes a knockout-stage form layer from official UEFA results, weighted separately through goals for and goals against. Formation selection changes the projected XI, applies XI/substitute minutes and start probabilities, and lightly adjusts team xG through a lineup-strength modifier. 
    
    Since this is a final, 90-minute draws are routed through extra time and then penalties to estimate who lifts the trophy.
    """)
