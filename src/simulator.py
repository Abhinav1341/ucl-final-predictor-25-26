from scipy.stats import poisson


def build_score_matrix(team_a_xg, team_b_xg, max_goals=7):
    scores = []

    for team_a_goals in range(max_goals + 1):
        for team_b_goals in range(max_goals + 1):
            probability = (
                poisson.pmf(team_a_goals, team_a_xg)
                * poisson.pmf(team_b_goals, team_b_xg)
            )

            scores.append(
                {
                    "team_a_goals": team_a_goals,
                    "team_b_goals": team_b_goals,
                    "probability": probability,
                }
            )

    return scores


def summarize_score_matrix(scores):
    team_a_win = 0
    draw = 0
    team_b_win = 0

    for row in scores:
        if row["team_a_goals"] > row["team_b_goals"]:
            team_a_win += row["probability"]
        elif row["team_a_goals"] == row["team_b_goals"]:
            draw += row["probability"]
        else:
            team_b_win += row["probability"]

    top_scorelines = sorted(
        scores,
        key=lambda row: row["probability"],
        reverse=True,
    )[:8]

    return {
        "team_a_win": team_a_win,
        "draw": draw,
        "team_b_win": team_b_win,
        "top_scorelines": top_scorelines,
    }


def summarize_final_winner(scores, team_a_xg, team_b_xg):
    summary = summarize_score_matrix(scores)
    draw_probability = summary["draw"]

    extra_time_team_a_xg = team_a_xg * (30 / 90) * 0.82
    extra_time_team_b_xg = team_b_xg * (30 / 90) * 0.82
    extra_time_scores = build_score_matrix(
        extra_time_team_a_xg,
        extra_time_team_b_xg,
        max_goals=4,
    )
    extra_time_summary = summarize_score_matrix(extra_time_scores)

    penalty_team_a = _penalty_shootout_probability(team_a_xg, team_b_xg)
    penalty_team_b = 1 - penalty_team_a

    penalties_probability = draw_probability * extra_time_summary["draw"]
    team_a_extra_time_win = draw_probability * extra_time_summary["team_a_win"]
    team_b_extra_time_win = draw_probability * extra_time_summary["team_b_win"]
    team_a_penalty_win = penalties_probability * penalty_team_a
    team_b_penalty_win = penalties_probability * penalty_team_b

    return {
        "team_a_lift_trophy": (
            summary["team_a_win"] + team_a_extra_time_win + team_a_penalty_win
        ),
        "team_b_lift_trophy": (
            summary["team_b_win"] + team_b_extra_time_win + team_b_penalty_win
        ),
        "extra_time_probability": draw_probability,
        "penalties_probability": penalties_probability,
        "team_a_extra_time_win": team_a_extra_time_win,
        "team_b_extra_time_win": team_b_extra_time_win,
        "team_a_penalty_win": team_a_penalty_win,
        "team_b_penalty_win": team_b_penalty_win,
    }


def _penalty_shootout_probability(team_a_xg, team_b_xg):
    total = team_a_xg + team_b_xg
    if total <= 0:
        return 0.5

    strength_edge = (team_a_xg - team_b_xg) / total
    probability = 0.5 + 0.12 * strength_edge
    return max(0.42, min(0.58, probability))
