import re

import pandas as pd

from src.data_loader import load_knockout_data, load_match_data


BASE_FINAL_XG = 1.35
TARGET_TEAMS = {"Arsenal", "PSG"}


def _parse_score(score):
    parts = re.split(r"[-–—]", str(score))
    if len(parts) != 2:
        raise ValueError(f"Could not parse score: {score}")
    return int(parts[0]), int(parts[1])


def _parse_made_total(value):
    match = re.search(r"(\d+)\s+of\s+(\d+)", str(value))
    if not match:
        return 0, 0
    return int(match.group(1)), int(match.group(2))


def _xg_proxy(shots, shots_on_target):
    return 0.06 * shots + 0.20 * shots_on_target


def _to_team_match_rows(matches):
    rows = []

    for _, match in matches.iterrows():
        home_goals, away_goals = _parse_score(match["score"])
        home_sot, home_shots = _parse_made_total(match["home_shots_on_target"])
        away_sot, away_shots = _parse_made_total(match["away_shots_on_target"])

        common = {
            "date": match.get("date"),
            "venue": match.get("venue"),
            "referee": match.get("referee"),
        }

        rows.append(
            {
                **common,
                "team": match["home_team"],
                "opponent": match["away_team"],
                "goals_for": home_goals,
                "goals_against": away_goals,
                "shots_for": home_shots,
                "shots_against": away_shots,
                "sot_for": home_sot,
                "sot_against": away_sot,
                "possession": match["home_possession"],
                "xg_proxy_for": _xg_proxy(home_shots, home_sot),
                "xg_proxy_against": _xg_proxy(away_shots, away_sot),
            }
        )
        rows.append(
            {
                **common,
                "team": match["away_team"],
                "opponent": match["home_team"],
                "goals_for": away_goals,
                "goals_against": home_goals,
                "shots_for": away_shots,
                "shots_against": home_shots,
                "sot_for": away_sot,
                "sot_against": home_sot,
                "possession": match["away_possession"],
                "xg_proxy_for": _xg_proxy(away_shots, away_sot),
                "xg_proxy_against": _xg_proxy(home_shots, home_sot),
            }
        )

    return pd.DataFrame(rows)


def load_team_stats():
    matches = load_match_data()
    team_matches = _to_team_match_rows(matches)
    relevant_matches = team_matches[team_matches["team"].isin(TARGET_TEAMS)].copy()

    stats = (
        relevant_matches.groupby("team")
        .agg(
            matches=("team", "size"),
            goals_for_per_match=("goals_for", "mean"),
            goals_against_per_match=("goals_against", "mean"),
            shots_for_per_match=("shots_for", "mean"),
            shots_against_per_match=("shots_against", "mean"),
            sot_for_per_match=("sot_for", "mean"),
            sot_against_per_match=("sot_against", "mean"),
            xg_proxy_for_per_match=("xg_proxy_for", "mean"),
            xg_proxy_against_per_match=("xg_proxy_against", "mean"),
            possession=("possession", "mean"),
        )
        .reset_index()
    )

    recent = (
        relevant_matches.sort_values("date")
        .groupby("team")
        .tail(5)
        .groupby("team")
        .agg(
            recent_xg_proxy_for=("xg_proxy_for", "mean"),
            recent_xg_proxy_against=("xg_proxy_against", "mean"),
        )
        .reset_index()
    )

    knockout_stats = _load_knockout_team_stats()

    return (
        stats.merge(recent, on="team", how="left")
        .merge(knockout_stats, on="team", how="left")
        .fillna(
            {
                "knockout_matches": 0,
                "knockout_goals_for_per_match": stats["goals_for_per_match"].mean(),
                "knockout_goals_against_per_match": stats[
                    "goals_against_per_match"
                ].mean(),
            }
        )
    )


def _load_knockout_team_stats():
    matches = load_knockout_data()
    rows = []

    for _, match in matches.iterrows():
        rows.append(
            {
                "team": match["home_team"],
                "goals_for": match["home_goals"],
                "goals_against": match["away_goals"],
            }
        )
        rows.append(
            {
                "team": match["away_team"],
                "goals_for": match["away_goals"],
                "goals_against": match["home_goals"],
            }
        )

    team_rows = pd.DataFrame(rows)
    team_rows = team_rows[team_rows["team"].isin(TARGET_TEAMS)]

    return (
        team_rows.groupby("team")
        .agg(
            knockout_matches=("team", "size"),
            knockout_goals_for_per_match=("goals_for", "mean"),
            knockout_goals_against_per_match=("goals_against", "mean"),
        )
        .reset_index()
    )


def get_team_row(team_stats, team_name):
    rows = team_stats[team_stats["team"] == team_name]

    if rows.empty:
        raise ValueError(f"No stats found for team: {team_name}")

    return rows.iloc[0]


def _safe_ratio(value, baseline):
    if pd.isna(value) or pd.isna(baseline) or baseline == 0:
        return 1.0
    return value / baseline


def calculate_expected_goals(team_a, team_b, team_stats):
    team_a_row = get_team_row(team_stats, team_a)
    team_b_row = get_team_row(team_stats, team_b)

    avg_xg_for = team_stats["xg_proxy_for_per_match"].mean()
    avg_xg_against = team_stats["xg_proxy_against_per_match"].mean()
    avg_goals_for = team_stats["goals_for_per_match"].mean()
    avg_sot_for = team_stats["sot_for_per_match"].mean()
    avg_knockout_goals_for = team_stats["knockout_goals_for_per_match"].mean()
    avg_knockout_goals_against = team_stats[
        "knockout_goals_against_per_match"
    ].mean()

    def attack_rating(row):
        season_xg = _safe_ratio(row["xg_proxy_for_per_match"], avg_xg_for)
        recent_xg = _safe_ratio(row["recent_xg_proxy_for"], avg_xg_for)
        goals = _safe_ratio(row["goals_for_per_match"], avg_goals_for)
        sot = _safe_ratio(row["sot_for_per_match"], avg_sot_for)
        knockout_goals = _safe_ratio(
            row["knockout_goals_for_per_match"], avg_knockout_goals_for
        )
        return (
            0.45 * season_xg
            + 0.15 * recent_xg
            + 0.12 * goals
            + 0.08 * sot
            + 0.20 * knockout_goals
        )

    def defense_weakness(row):
        season_xg = _safe_ratio(row["xg_proxy_against_per_match"], avg_xg_against)
        recent_xg = _safe_ratio(row["recent_xg_proxy_against"], avg_xg_against)
        knockout_goals = _safe_ratio(
            row["knockout_goals_against_per_match"], avg_knockout_goals_against
        )
        return 0.55 * season_xg + 0.20 * recent_xg + 0.25 * knockout_goals

    team_a_xg = BASE_FINAL_XG * attack_rating(team_a_row) * defense_weakness(team_b_row)
    team_b_xg = BASE_FINAL_XG * attack_rating(team_b_row) * defense_weakness(team_a_row)

    return round(team_a_xg, 2), round(team_b_xg, 2)
