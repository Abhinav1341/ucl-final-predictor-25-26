from src.predict import predict_match


prediction = predict_match("Arsenal", "PSG")

print(f"{prediction['team_a']} xG: {prediction['team_a_xg']}")
print(f"{prediction['team_b']} xG: {prediction['team_b_xg']}")
print()
print(f"{prediction['team_a']} win: {prediction['team_a_win']:.1%}")
print(f"Draw: {prediction['draw']:.1%}")
print(f"{prediction['team_b']} win: {prediction['team_b_win']:.1%}")
print()
print("Most likely scorelines:")

for scoreline in prediction["top_scorelines"]:
    print(
        f"{prediction['team_a']} {scoreline['team_a_goals']}-"
        f"{scoreline['team_b_goals']} {prediction['team_b']}: "
        f"{scoreline['probability']:.1%}"
    )

print()
print("Likely scorers:")

for scorer in prediction["scorers"][:8]:
    print(
        f"{scorer['player']} ({scorer['team']}): "
        f"{scorer['goal_probability']:.1%} "
        f"xG={scorer['player_xg']:.2f}"
    )
