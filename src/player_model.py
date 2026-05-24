import math

import pandas as pd

from src.data_loader import load_player_data


DEFAULT_EXPECTED_MINUTES = {
    "Goalkeeper": 90,
    "Defender": 84,
    "Midfielder": 78,
    "Forward": 74,
    "Attacker": 74,
}

PER_90_COLUMNS = [
    "clear_chances",
    "penalties_scored",
    "penalties_awarded",
    "corners_taken",
    "key_attacking_runs",
    "passes_into_penalty_area",
]

DEFAULT_FORMATIONS = {
    "Arsenal": "4-3-3",
    "PSG": "4-3-3",
}

FORMATION_SLOTS = {
    "4-3-3": {"Goalkeeper": 1, "Defender": 4, "Midfielder": 3, "Forward": 3},
    "4-2-3-1": {"Goalkeeper": 1, "Defender": 4, "Midfielder": 5, "Forward": 1},
    "4-4-2": {"Goalkeeper": 1, "Defender": 4, "Midfielder": 4, "Forward": 2},
    "3-4-3": {"Goalkeeper": 1, "Defender": 3, "Midfielder": 4, "Forward": 3},
}

POSITION_FLEXIBILITY = {
    "Goalkeeper": {"Goalkeeper": 1.00},
    "Defender": {"Defender": 1.00, "Midfielder": 0.82, "Forward": 0.58},
    "Midfielder": {"Midfielder": 1.00, "Defender": 0.78, "Forward": 0.86},
    "Forward": {"Forward": 1.00, "Midfielder": 0.84, "Defender": 0.55},
}


def load_player_stats():
    players = load_player_data()
    players = players[players["club"].isin(["Arsenal", "PSG"])].copy()
    players = players.rename(
        columns={
            "player_name": "player",
            "club": "team",
            "matches_played": "ucl_matches_played",
            "minutes_played": "ucl_minutes_played",
            "goals": "ucl_goals",
            "assists": "ucl_assists",
        }
    )

    numeric_columns = [
        "ucl_matches_played",
        "ucl_minutes_played",
        "ucl_goals",
        "ucl_assists",
        "clear_chances",
        "penalties_scored",
        "penalties_awarded",
        "corners_taken",
        "key_attacking_runs",
        "passes_into_penalty_area",
    ]
    for column in numeric_columns:
        if column in players.columns:
            players[column] = pd.to_numeric(players[column], errors="coerce").fillna(0)

    players["goals_per_90"] = (
        players["ucl_goals"] / players["ucl_minutes_played"].replace(0, pd.NA) * 90
    ).fillna(0)
    players["assists_per_90"] = (
        players["ucl_assists"] / players["ucl_minutes_played"].replace(0, pd.NA) * 90
    ).fillna(0)

    for column in PER_90_COLUMNS:
        players[f"{column}_per_90"] = (
            players[column] / players["ucl_minutes_played"].replace(0, pd.NA) * 90
        ).fillna(0)

    players["high_goal_boost"] = players.apply(_high_goal_attacker_boost, axis=1)

    players["attacking_score"] = (
        0.70 * players["goals_per_90"]
        + 0.12 * players["clear_chances_per_90"]
        + 0.06 * players["key_attacking_runs_per_90"]
        + 0.05 * players["passes_into_penalty_area_per_90"]
        + 0.04 * players["assists_per_90"]
        + 0.03 * players["penalties_scored_per_90"]
    )
    players["attacking_score"] *= players["high_goal_boost"]
    players.loc[players["position"].isin(["Goalkeeper", "Defender"]), "attacking_score"] *= 0.45
    players["attacking_score"] = players["attacking_score"].clip(lower=0.01)

    players["creative_score"] = (
        0.45 * players["assists_per_90"]
        + 0.20 * players["passes_into_penalty_area_per_90"]
        + 0.15 * players["key_attacking_runs_per_90"]
        + 0.10 * players["clear_chances_per_90"]
        + 0.10 * players["corners_taken_per_90"]
    )
    players.loc[players["position"].eq("Goalkeeper"), "creative_score"] *= 0.05
    players.loc[players["position"].eq("Defender"), "creative_score"] *= 0.65
    players["creative_score"] = players["creative_score"].clip(lower=0.01)

    players["expected_minutes"] = players.apply(_estimate_expected_minutes, axis=1)
    players["starting_probability"] = players.apply(_estimate_starting_probability, axis=1)
    players["penalty_boost"] = players["penalties_scored"].clip(upper=2) * 0.015

    players["xg_share"] = players.groupby("team")["attacking_score"].transform(
        lambda values: values / values.sum()
    )
    players["assist_share"] = players.groupby("team")["creative_score"].transform(
        lambda values: values / values.sum()
    )

    return players


def _high_goal_attacker_boost(player):
    if player["position"] not in ["Forward", "Attacker"]:
        return 1.0
    if player["ucl_goals"] >= 8:
        return 1.18
    if player["ucl_goals"] >= 5:
        return 1.10
    if player["ucl_goals"] >= 3:
        return 1.05
    return 1.0


def _estimate_expected_minutes(player):
    minutes_per_match = 0
    if player["ucl_matches_played"] > 0:
        minutes_per_match = player["ucl_minutes_played"] / player["ucl_matches_played"]

    default_minutes = DEFAULT_EXPECTED_MINUTES.get(player["position"], 72)
    estimated = 0.65 * minutes_per_match + 0.35 * default_minutes
    return round(max(12, min(90, estimated)), 0)


def _estimate_starting_probability(player):
    if player["ucl_matches_played"] == 0:
        return 0.25

    minutes_per_match = player["ucl_minutes_played"] / player["ucl_matches_played"]
    probability = 0.25 + (minutes_per_match / 90) * 0.75
    return round(max(0.15, min(0.98, probability)), 2)


def calculate_player_goal_probabilities(team, team_xg, player_stats):
    team_players = player_stats[player_stats["team"] == team].copy()

    if team_players.empty:
        raise ValueError(f"No player stats found for team: {team}")

    team_players["minutes_factor"] = team_players["expected_minutes"] / 90

    team_players["player_xg"] = (
        team_xg
        * team_players["xg_share"]
        * team_players["minutes_factor"]
        * team_players["starting_probability"]
    ) + team_players["penalty_boost"]

    team_players["scorer_reason"] = team_players.apply(_build_scorer_reason, axis=1)

    team_players["goal_probability"] = team_players["player_xg"].apply(
        lambda xg: 1 - math.exp(-xg)
    )

    team_players = team_players.sort_values(
        "goal_probability",
        ascending=False,
    )

    return team_players[
        [
            "player",
            "team",
            "position",
            "expected_minutes",
            "ucl_goals",
            "ucl_assists",
            "goals_per_90",
            "clear_chances_per_90",
            "key_attacking_runs_per_90",
            "starting_probability",
            "high_goal_boost",
            "xg_share",
            "player_xg",
            "goal_probability",
            "scorer_reason",
        ]
    ].to_dict("records")


def calculate_player_assist_probabilities(team, team_xg, player_stats):
    team_players = player_stats[player_stats["team"] == team].copy()

    if team_players.empty:
        raise ValueError(f"No player stats found for team: {team}")

    team_players["minutes_factor"] = team_players["expected_minutes"] / 90
    assisted_xg = team_xg * 0.72
    team_players["player_xa"] = (
        assisted_xg
        * team_players["assist_share"]
        * team_players["minutes_factor"]
        * team_players["starting_probability"]
    )
    team_players["assist_probability"] = team_players["player_xa"].apply(
        lambda xa: 1 - math.exp(-xa)
    )
    team_players["assist_reason"] = team_players.apply(_build_assist_reason, axis=1)

    team_players = team_players.sort_values(
        "assist_probability",
        ascending=False,
    )

    return team_players[
        [
            "player",
            "team",
            "position",
            "expected_minutes",
            "ucl_assists",
            "assists_per_90",
            "passes_into_penalty_area_per_90",
            "key_attacking_runs_per_90",
            "corners_taken_per_90",
            "starting_probability",
            "assist_share",
            "player_xa",
            "assist_probability",
            "assist_reason",
        ]
    ].to_dict("records")


def project_matchday_squad(team, player_stats, formation=None, substitutes_count=9):
    team_players = player_stats[player_stats["team"] == team].copy()

    if team_players.empty:
        raise ValueError(f"No player stats found for team: {team}")

    formation = formation or DEFAULT_FORMATIONS.get(team, "4-3-3")
    slots = FORMATION_SLOTS.get(formation, FORMATION_SLOTS["4-3-3"])
    team_players["lineup_bucket"] = team_players["position"].map(_lineup_bucket)
    team_players["lineup_score"] = (
        0.65 * team_players["expected_minutes"]
        + 35 * team_players["starting_probability"]
        + 0.25 * team_players["ucl_matches_played"]
    )

    selected = []
    selected_names = set()

    for bucket, count in slots.items():
        bucket_players = _rank_players_for_bucket(
            team_players=team_players,
            bucket=bucket,
            selected_names=selected_names,
        )
        picks = bucket_players.head(count)
        selected.extend(picks.to_dict("records"))
        selected_names.update(picks["player"].tolist())

    if len(selected) < 11:
        remaining = team_players[~team_players["player"].isin(selected_names)].sort_values(
            "lineup_score", ascending=False
        )
        fill_count = 11 - len(selected)
        selected.extend(remaining.head(fill_count).to_dict("records"))
        selected_names.update(remaining.head(fill_count)["player"].tolist())

    substitutes = team_players[~team_players["player"].isin(selected_names)].sort_values(
        "lineup_score", ascending=False
    ).copy()
    substitutes["assigned_role"] = substitutes["lineup_bucket"]
    substitutes["role_fit"] = 1.0

    return {
        "formation": formation,
        "likely_xi": _squad_rows(pd.DataFrame(selected)),
        "substitutes": _squad_rows(substitutes.head(substitutes_count)),
    }


def apply_lineup_context(team, player_stats, squad_projection):
    adjusted = player_stats.copy()
    xi_names = {player["player"] for player in squad_projection["likely_xi"]}
    substitute_names = {player["player"] for player in squad_projection["substitutes"]}
    team_mask = adjusted["team"].eq(team)

    adjusted.loc[team_mask, "lineup_status"] = "Outside squad"
    adjusted.loc[team_mask & adjusted["player"].isin(xi_names), "lineup_status"] = "XI"
    adjusted.loc[
        team_mask & adjusted["player"].isin(substitute_names), "lineup_status"
    ] = "Substitute"

    xi_mask = team_mask & adjusted["player"].isin(xi_names)
    sub_mask = team_mask & adjusted["player"].isin(substitute_names)
    outside_mask = team_mask & ~(adjusted["player"].isin(xi_names | substitute_names))

    adjusted.loc[xi_mask, "starting_probability"] = adjusted.loc[
        xi_mask, "starting_probability"
    ].clip(lower=0.88, upper=0.98)
    adjusted.loc[xi_mask, "expected_minutes"] = adjusted.loc[
        xi_mask, "expected_minutes"
    ].clip(lower=68, upper=90)

    adjusted.loc[sub_mask, "starting_probability"] = adjusted.loc[
        sub_mask, "starting_probability"
    ].clip(upper=0.12)
    adjusted.loc[sub_mask, "expected_minutes"] = adjusted.loc[
        sub_mask, "expected_minutes"
    ].clip(upper=24)

    adjusted.loc[outside_mask, "starting_probability"] = adjusted.loc[
        outside_mask, "starting_probability"
    ].clip(upper=0.02)
    adjusted.loc[outside_mask, "expected_minutes"] = adjusted.loc[
        outside_mask, "expected_minutes"
    ].clip(upper=3)

    return adjusted


def calculate_lineup_xg_modifier(team, player_stats, squad_projection):
    team_players = player_stats[player_stats["team"].eq(team)].copy()
    xi_names = {player["player"] for player in squad_projection["likely_xi"]}

    team_players["lineup_value"] = (
        team_players["attacking_score"] + 0.35 * team_players["creative_score"]
    )
    team_players["lineup_bucket"] = team_players["position"].map(_lineup_bucket)

    selected_value = team_players[
        team_players["player"].isin(xi_names)
    ]["lineup_value"].sum()
    slots = FORMATION_SLOTS.get(
        squad_projection["formation"],
        FORMATION_SLOTS["4-3-3"],
    )
    baseline_parts = []
    for bucket, count in slots.items():
        baseline_parts.append(
            _rank_players_for_bucket(
                team_players=team_players,
                bucket=bucket,
                selected_names=set(),
                score_column="lineup_value",
            )
            .head(count)
        )
    baseline = pd.concat(baseline_parts)
    if len(baseline) < 11:
        remaining = team_players[~team_players["player"].isin(baseline["player"])]
        baseline = pd.concat(
            [
                baseline,
                remaining.sort_values("lineup_value", ascending=False).head(
                    11 - len(baseline)
                ),
            ]
        )
    baseline_value = baseline["lineup_value"].sum()

    if baseline_value <= 0:
        return 1.0

    raw_modifier = selected_value / baseline_value
    return round(max(0.92, min(1.08, raw_modifier)), 3)


def _rank_players_for_bucket(
    team_players,
    bucket,
    selected_names,
    score_column="lineup_score",
):
    candidates = team_players[~team_players["player"].isin(selected_names)].copy()
    candidates["role_fit"] = candidates["lineup_bucket"].apply(
        lambda player_bucket: _role_fit(player_bucket, bucket)
    )
    candidates = candidates[candidates["role_fit"] > 0]
    candidates["role_adjusted_score"] = candidates[score_column] * candidates[
        "role_fit"
    ]
    candidates["assigned_role"] = bucket

    return candidates.sort_values(
        ["role_fit", "role_adjusted_score"],
        ascending=[False, False],
    )


def _role_fit(player_bucket, target_bucket):
    return POSITION_FLEXIBILITY.get(player_bucket, {}).get(target_bucket, 0)


def _lineup_bucket(position):
    if position == "Goalkeeper":
        return "Goalkeeper"
    if position == "Defender":
        return "Defender"
    if position in ["Forward", "Attacker"]:
        return "Forward"
    return "Midfielder"


def _squad_rows(players):
    if players.empty:
        return []

    return players[
        [
            "player",
            "team",
            "position",
            "assigned_role",
            "role_fit",
            "expected_minutes",
            "starting_probability",
            "ucl_matches_played",
            "ucl_minutes_played",
            "ucl_goals",
            "ucl_assists",
        ]
    ].to_dict("records")


def _build_scorer_reason(player):
    reasons = [
        f"{player['ucl_goals']:.0f} UCL goals",
        f"{player['goals_per_90']:.2f} goals/90",
        f"{player['expected_minutes']:.0f} projected minutes",
        f"{player['starting_probability']:.0%} start chance",
    ]

    if player["high_goal_boost"] > 1:
        reasons.append(f"{player['high_goal_boost']:.2f}x high-goal boost")

    return ", ".join(reasons)


def _build_assist_reason(player):
    return ", ".join(
        [
            f"{player['ucl_assists']:.0f} UCL assists",
            f"{player['assists_per_90']:.2f} assists/90",
            f"{player['passes_into_penalty_area_per_90']:.2f} penalty-area passes/90",
            f"{player['expected_minutes']:.0f} projected minutes",
        ]
    )
