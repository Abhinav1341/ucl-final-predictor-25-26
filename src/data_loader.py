from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
MATCH_FILE = RAW_DATA_DIR / "Away Games - League Stage.xlsx"
PLAYER_FILE = RAW_DATA_DIR / "UCL Final Matchup Stats.xlsx"
KNOCKOUT_FILE = PROCESSED_DATA_DIR / "knockout_matches.csv"

TEAM_ALIASES = {
    "PSG": "PSG",
    "Paris": "PSG",
    "Paris Saint-Germain": "PSG",
    "Arsenal": "Arsenal",
}


def normalize_team(team):
    return TEAM_ALIASES.get(str(team).strip(), str(team).strip())


def load_match_data(path=MATCH_FILE):
    matches = pd.read_excel(path, sheet_name="champions_league_matches")
    matches = matches.copy()
    matches = matches.dropna(subset=["home_team", "away_team", "score"])
    matches["home_team"] = matches["home_team"].map(normalize_team)
    matches["away_team"] = matches["away_team"].map(normalize_team)
    return matches


def load_player_data(path=PLAYER_FILE):
    players = pd.read_excel(path, sheet_name="ucl_squad_stats_cleaned")
    players = players.copy()
    players["club"] = players["club"].map(normalize_team)
    return players


def load_knockout_data(path=KNOCKOUT_FILE):
    matches = pd.read_csv(path, parse_dates=["date"])
    matches = matches.copy()
    matches["home_team"] = matches["home_team"].map(normalize_team)
    matches["away_team"] = matches["away_team"].map(normalize_team)
    return matches


def knockout_rows_for_display(path=KNOCKOUT_FILE):
    matches = load_knockout_data(path)
    matches["score"] = (
        matches["home_goals"].astype(str) + "-" + matches["away_goals"].astype(str)
    )
    return matches[
        [
            "date",
            "stage",
            "home_team",
            "away_team",
            "score",
            "source",
        ]
    ].to_dict("records")
