import pandas as pd
import streamlit as st

from src.predict import predict_match


st.set_page_config(
    page_title="UCL Predictor",
    page_icon="UCL",
    layout="wide",
)

st.title("UCL Match Predictor")

team_options = ["Arsenal", "PSG"]
formation_options = ["4-3-3", "4-2-3-1", "4-4-2", "3-4-3"]

left, right = st.columns(2)

with left:
    team_a = st.selectbox("Team A", team_options, index=0)
    team_a_formation = st.selectbox(
        f"{team_a} formation",
        formation_options,
        index=0,
        key="team_a_formation",
    )

with right:
    team_b = st.selectbox("Team B", team_options, index=1)
    team_b_formation = st.selectbox(
        f"{team_b} formation",
        formation_options,
        index=0,
        key="team_b_formation",
    )

if team_a == team_b:
    st.warning("Choose two different teams.")
    st.stop()

prediction = predict_match(
    team_a,
    team_b,
    team_a_formation=team_a_formation,
    team_b_formation=team_b_formation,
)

st.divider()

metric_1, metric_2, metric_3 = st.columns(3)

with metric_1:
    st.metric(f"{team_a} win", f"{prediction['team_a_win']:.1%}")

with metric_2:
    st.metric("Draw", f"{prediction['draw']:.1%}")

with metric_3:
    st.metric(f"{team_b} win", f"{prediction['team_b_win']:.1%}")

st.divider()

st.subheader("Final winner path")
winner_1, winner_2, winner_3, winner_4 = st.columns(4)

with winner_1:
    st.metric(f"{team_a} lift trophy", f"{prediction['team_a_lift_trophy']:.1%}")

with winner_2:
    st.metric(f"{team_b} lift trophy", f"{prediction['team_b_lift_trophy']:.1%}")

with winner_3:
    st.metric("Extra time", f"{prediction['extra_time_probability']:.1%}")

with winner_4:
    st.metric("Penalties", f"{prediction['penalties_probability']:.1%}")

path_rows = [
    {"Path": f"{team_a} win in 90", "Probability": f"{prediction['team_a_win']:.1%}"},
    {"Path": f"{team_b} win in 90", "Probability": f"{prediction['team_b_win']:.1%}"},
    {
        "Path": f"{team_a} win in extra time",
        "Probability": f"{prediction['team_a_extra_time_win']:.1%}",
    },
    {
        "Path": f"{team_b} win in extra time",
        "Probability": f"{prediction['team_b_extra_time_win']:.1%}",
    },
    {
        "Path": f"{team_a} win on penalties",
        "Probability": f"{prediction['team_a_penalty_win']:.1%}",
    },
    {
        "Path": f"{team_b} win on penalties",
        "Probability": f"{prediction['team_b_penalty_win']:.1%}",
    },
]
st.dataframe(pd.DataFrame(path_rows), hide_index=True, use_container_width=True)

st.divider()

xg_1, xg_2 = st.columns(2)

with xg_1:
    st.subheader(f"{team_a} expected goals")
    st.metric("xG", prediction["team_a_xg"])
    st.caption(f"Lineup modifier: {prediction['team_a_lineup_modifier']:.3f}x")

with xg_2:
    st.subheader(f"{team_b} expected goals")
    st.metric("xG", prediction["team_b_xg"])
    st.caption(f"Lineup modifier: {prediction['team_b_lineup_modifier']:.3f}x")

st.divider()

scoreline_rows = []
for scoreline in prediction["top_scorelines"]:
    scoreline_rows.append(
        {
            "Scoreline": (
                f"{team_a} {scoreline['team_a_goals']}-"
                f"{scoreline['team_b_goals']} {team_b}"
            ),
            "Probability": f"{scoreline['probability']:.1%}",
        }
    )
scoreline_df = pd.DataFrame(scoreline_rows)

scorer_rows = []
for scorer in prediction["scorers"]:
    scorer_rows.append(
        {
            "Player": scorer["player"],
            "Team": scorer["team"],
            "Position": scorer["position"],
            "Expected minutes": scorer["expected_minutes"],
            "UCL goals": scorer["ucl_goals"],
            "UCL assists": scorer["ucl_assists"],
            "Goals/90": round(scorer["goals_per_90"], 2),
            "Clear chances/90": round(scorer["clear_chances_per_90"], 2),
            "Start chance": f"{scorer['starting_probability']:.0%}",
            "Goal boost": f"{scorer['high_goal_boost']:.2f}x",
            "xG share": f"{scorer['xg_share']:.1%}",
            "Player xG": round(scorer["player_xg"], 2),
            "Goal probability": f"{scorer['goal_probability']:.1%}",
            "Why": scorer["scorer_reason"],
        }
    )
scorer_df = pd.DataFrame(scorer_rows)

assist_rows = []
for assister in prediction["assisters"]:
    assist_rows.append(
        {
            "Player": assister["player"],
            "Team": assister["team"],
            "Position": assister["position"],
            "Expected minutes": assister["expected_minutes"],
            "UCL assists": assister["ucl_assists"],
            "Assists/90": round(assister["assists_per_90"], 2),
            "Penalty-area passes/90": round(
                assister["passes_into_penalty_area_per_90"], 2
            ),
            "Corners/90": round(assister["corners_taken_per_90"], 2),
            "Start chance": f"{assister['starting_probability']:.0%}",
            "Assist share": f"{assister['assist_share']:.1%}",
            "Player xA": round(assister["player_xa"], 2),
            "Assist probability": f"{assister['assist_probability']:.1%}",
            "Why": assister["assist_reason"],
        }
    )
assist_df = pd.DataFrame(assist_rows)

table_1, table_2 = st.columns(2)

with table_1:
    st.subheader("Most likely scorelines")
    st.dataframe(scoreline_df, hide_index=True, use_container_width=True)

with table_2:
    st.subheader("Likely scorers")
    st.dataframe(scorer_df.head(10), hide_index=True, use_container_width=True)

st.divider()

st.subheader("Likely assists")
st.dataframe(assist_df.head(12), hide_index=True, use_container_width=True)

st.divider()


def squad_dataframe(rows):
    return pd.DataFrame(
        [
            {
                "Player": row["player"],
                "Position": row["position"],
                "Role": row.get("assigned_role", row["position"]),
                "Role fit": f"{row.get('role_fit', 1):.0%}",
                "Expected minutes": row["expected_minutes"],
                "Start chance": f"{row['starting_probability']:.0%}",
                "UCL matches": row["ucl_matches_played"],
                "UCL minutes": row["ucl_minutes_played"],
                "UCL goals": row["ucl_goals"],
                "UCL assists": row["ucl_assists"],
            }
            for row in rows
        ]
    )


xi_1, xi_2 = st.columns(2)

with xi_1:
    st.subheader(f"{team_a} likely XI")
    st.caption(prediction["team_a_squad"]["formation"])
    st.dataframe(
        squad_dataframe(prediction["team_a_squad"]["likely_xi"]),
        hide_index=True,
        use_container_width=True,
    )
    st.subheader(f"{team_a} substitutes")
    st.dataframe(
        squad_dataframe(prediction["team_a_squad"]["substitutes"]),
        hide_index=True,
        use_container_width=True,
    )

with xi_2:
    st.subheader(f"{team_b} likely XI")
    st.caption(prediction["team_b_squad"]["formation"])
    st.dataframe(
        squad_dataframe(prediction["team_b_squad"]["likely_xi"]),
        hide_index=True,
        use_container_width=True,
    )
    st.subheader(f"{team_b} substitutes")
    st.dataframe(
        squad_dataframe(prediction["team_b_squad"]["substitutes"]),
        hide_index=True,
        use_container_width=True,
    )

st.divider()

st.subheader("Team data snapshot")
team_stats_df = pd.DataFrame(prediction["team_stats"])
team_stats_df = team_stats_df[
    [
        "team",
        "matches",
        "goals_for_per_match",
        "goals_against_per_match",
        "shots_for_per_match",
        "sot_for_per_match",
        "xg_proxy_for_per_match",
        "xg_proxy_against_per_match",
        "knockout_matches",
        "knockout_goals_for_per_match",
        "knockout_goals_against_per_match",
        "possession",
    ]
].round(2)
st.dataframe(team_stats_df, hide_index=True, use_container_width=True)

st.subheader("Knockout stage scores")
knockout_df = pd.DataFrame(prediction["knockout_matches"])
knockout_df["date"] = pd.to_datetime(knockout_df["date"]).dt.strftime("%Y-%m-%d")
st.dataframe(
    knockout_df[
        [
            "date",
            "stage",
            "home_team",
            "away_team",
            "score",
        ]
    ],
    hide_index=True,
    use_container_width=True,
)

st.divider()

st.subheader("Model notes")
st.write(
    f"""
This version uses your Excel workbooks as the primary data source. Team strength is
derived from UCL league-stage goals, possession, shots, shots on target, and a simple
xG proxy. It also includes a knockout-stage form layer from official UEFA results,
weighted separately through goals for and goals against. Formation selection changes
the projected XI, applies XI/substitute minutes and start probabilities, and lightly
adjusts team xG through a lineup-strength modifier. Player goal and assist
probabilities then use those adjusted team and player inputs.
Since this is a final, 90-minute draws are routed through extra time and then
penalties to estimate who lifts the trophy.

Current prediction: {team_a} are projected for **{prediction['team_a_xg']} xG** and
{team_b} are projected for **{prediction['team_b_xg']} xG**.
"""
)
