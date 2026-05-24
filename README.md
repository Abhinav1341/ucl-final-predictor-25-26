# UCL Final Predictor

A Streamlit app that predicts a UEFA Champions League final matchup using team form,
player-level UCL data, formation-aware lineups, likely scorers, likely assisters,
extra time, and penalty paths.

The current demo is built around an Arsenal vs PSG final scenario and uses local
Excel/CSV data as the primary source.

## Features

- 90-minute win/draw/loss probabilities
- Trophy probabilities after extra time and penalties
- Expected goals for both teams
- Most likely scorelines
- Formation-aware likely XI
- Substitutes with reduced expected minutes
- Flexible player role fitting across adjacent positions
- Likely scorer probabilities
- Likely assist probabilities
- Team data snapshot
- Knockout-stage score table
- Lineup-strength modifiers that affect team xG

## Model Flow

```text
Select teams and formations
  -> Build formation-aware likely XI and substitutes
  -> Apply role-fit and minutes adjustments
  -> Estimate team xG from league-stage and knockout data
  -> Apply lineup-strength modifier
  -> Simulate 90-minute scorelines with Poisson probabilities
  -> Route draws through extra time
  -> Route extra-time draws through penalties
  -> Allocate team xG/xA to players
  -> Display team, scoreline, scorer, assister, and squad outputs
```

## Data

The app uses data from:

- `data/raw/Away Games - League Stage.xlsx`
- `data/raw/Home Games - League Stage.xlsx`
- `data/raw/UCL Final Matchup Stats.xlsx`
- `data/processed/knockout_matches.csv`

The league-stage workbook provides match-level data such as:

- goals
- possession
- shots on target
- total attempts
- saves

The player workbook provides UCL squad data such as:

- player name
- club
- position
- matches played
- minutes played
- goals
- assists
- attacking involvement
- passing into penalty area
- corners
- defensive and goalkeeping stats

The knockout CSV contains the knockout-stage scoreline layer used for high-pressure
form adjustment.

## Important Modeling Note

The available fixture data does not include official xG. The app therefore uses a
transparent xG proxy:

```python
xg_proxy = 0.06 * total_shots + 0.20 * shots_on_target
```

This is useful for a weekend MVP, but it should be replaced with real xG from a
licensed or reliable public data source when available.

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

Run a CLI prediction:

```powershell
python main.py
```

Run the Streamlit app:

```powershell
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## Streamlit Cloud Deployment

1. Push this project to GitHub.
2. Go to Streamlit Community Cloud.
3. Create a new app from the GitHub repository.
4. Set the main file path to:

```text
app.py
```

5. Deploy.

Streamlit Cloud will install dependencies from `requirements.txt`.

## Project Structure

```text
UCL-Predictor/
  app.py
  main.py
  requirements.txt
  README.md
  data/
    raw/
      Away Games - League Stage.xlsx
      Home Games - League Stage.xlsx
      UCL Final Matchup Stats.xlsx
    processed/
      knockout_matches.csv
      player_stats.csv
      team_stats.csv
  src/
    data_loader.py
    player_model.py
    predict.py
    simulator.py
    team_model.py
```

## Core Files

- `src/data_loader.py`: loads Excel/CSV source data with portable repo-relative paths.
- `src/team_model.py`: builds team-level expected goals from league-stage and knockout data.
- `src/player_model.py`: projects lineups, substitutes, player scorer probabilities, and assist probabilities.
- `src/simulator.py`: simulates scorelines, extra time, penalties, and trophy probability.
- `src/predict.py`: orchestrates the full prediction pipeline.
- `app.py`: Streamlit dashboard.
- `main.py`: quick command-line prediction.

## Formation and Role Flexibility

The lineup engine supports these formations:

- `4-3-3`
- `4-2-3-1`
- `4-4-2`
- `3-4-3`

Players can fill adjacent roles with a role-fit penalty:

- Defender -> Midfielder / Forward
- Midfielder -> Defender / Forward
- Forward or Attacker -> Midfielder / Defender
- Goalkeeper -> Goalkeeper only

This makes the XI builder more realistic while still preferring natural-position
players.

## Final Winner Logic

The model separates:

- 90-minute win probability
- draw probability
- extra-time win probability
- penalty probability
- final trophy probability

This matters because a final cannot end in a draw.

## Limitations

- The model uses an xG proxy, not official xG.
- Player roles are broad, not exact tactical zones.
- Injuries, suspensions, press conferences, and confirmed lineups are not automated yet.
- Penalty shootout probabilities are simplified.
- Bookmaker odds are not yet used for calibration.
- Data quality directly controls prediction quality.

## Future Improvements

- Replace xG proxy with official or StatsBomb-style xG.
- Add injuries and suspensions.
- Add market-odds calibration.
- Add player-vs-player matchup adjustments.
- Add historical backtesting and Brier/log-loss scoring.
- Add tactical style inputs such as pressing, transition threat, and set-piece strength.
- Add confidence intervals.

## Disclaimer

This is a football analytics project for experimentation and learning. It is not
betting advice.
