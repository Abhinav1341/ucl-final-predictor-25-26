from src.player_model import (
    apply_lineup_context,
    calculate_lineup_xg_modifier,
    calculate_player_assist_probabilities,
    calculate_player_goal_probabilities,
    load_player_stats,
    project_matchday_squad,
)
from src.simulator import (
    build_score_matrix,
    summarize_final_winner,
    summarize_score_matrix,
)
from src.team_model import calculate_expected_goals, load_team_stats
from src.data_loader import knockout_rows_for_display


def predict_match(team_a, team_b, team_a_formation="4-3-3", team_b_formation="4-3-3"):
    team_stats = load_team_stats()
    player_stats = load_player_stats()

    team_a_xg, team_b_xg = calculate_expected_goals(
        team_a=team_a,
        team_b=team_b,
        team_stats=team_stats,
    )

    team_a_squad = project_matchday_squad(
        team=team_a,
        player_stats=player_stats,
        formation=team_a_formation,
    )
    team_b_squad = project_matchday_squad(
        team=team_b,
        player_stats=player_stats,
        formation=team_b_formation,
    )

    team_a_lineup_modifier = calculate_lineup_xg_modifier(
        team=team_a,
        player_stats=player_stats,
        squad_projection=team_a_squad,
    )
    team_b_lineup_modifier = calculate_lineup_xg_modifier(
        team=team_b,
        player_stats=player_stats,
        squad_projection=team_b_squad,
    )
    team_a_xg = round(team_a_xg * team_a_lineup_modifier, 2)
    team_b_xg = round(team_b_xg * team_b_lineup_modifier, 2)

    player_stats = apply_lineup_context(
        team=team_a,
        player_stats=player_stats,
        squad_projection=team_a_squad,
    )
    player_stats = apply_lineup_context(
        team=team_b,
        player_stats=player_stats,
        squad_projection=team_b_squad,
    )

    score_matrix = build_score_matrix(team_a_xg, team_b_xg)
    summary = summarize_score_matrix(score_matrix)
    final_summary = summarize_final_winner(score_matrix, team_a_xg, team_b_xg)

    team_a_scorers = calculate_player_goal_probabilities(
        team=team_a,
        team_xg=team_a_xg,
        player_stats=player_stats,
    )

    team_b_scorers = calculate_player_goal_probabilities(
        team=team_b,
        team_xg=team_b_xg,
        player_stats=player_stats,
    )
    team_a_assisters = calculate_player_assist_probabilities(
        team=team_a,
        team_xg=team_a_xg,
        player_stats=player_stats,
    )
    team_b_assisters = calculate_player_assist_probabilities(
        team=team_b,
        team_xg=team_b_xg,
        player_stats=player_stats,
    )

    scorers = sorted(
        team_a_scorers + team_b_scorers,
        key=lambda row: row["goal_probability"],
        reverse=True,
    )
    assisters = sorted(
        team_a_assisters + team_b_assisters,
        key=lambda row: row["assist_probability"],
        reverse=True,
    )

    return {
        "team_a": team_a,
        "team_b": team_b,
        "team_a_xg": team_a_xg,
        "team_b_xg": team_b_xg,
        "team_a_formation": team_a_formation,
        "team_b_formation": team_b_formation,
        "team_a_lineup_modifier": team_a_lineup_modifier,
        "team_b_lineup_modifier": team_b_lineup_modifier,
        "team_a_squad": team_a_squad,
        "team_b_squad": team_b_squad,
        "scorers": scorers,
        "assisters": assisters,
        "team_stats": team_stats.to_dict("records"),
        "knockout_matches": knockout_rows_for_display(),
        **final_summary,
        **summary,
    }
