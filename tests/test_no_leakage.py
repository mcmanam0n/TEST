import pandas as pd
from ncaam_sim.features.possessions import add_possessions
from ncaam_sim.features.four_factors import add_four_factors
from ncaam_sim.features.dataset_builder import build_training_rows


def test_walk_forward_no_leakage():
    games = pd.DataFrame([
        {'game_id': '1', 'date': '2025-11-01', 'season': 2026, 'neutral': 0, 'home_team': 'A', 'away_team': 'B',
         'home_score': 70, 'away_score': 60, 'home_FGA': 60, 'home_FGM': 25, 'home_3PA': 20, 'home_3PM': 8,
         'home_FTA': 18, 'home_ORB': 9, 'home_DRB': 24, 'home_TO': 10, 'away_FGA': 55, 'away_FGM': 22,
         'away_3PA': 18, 'away_3PM': 6, 'away_FTA': 15, 'away_ORB': 7, 'away_DRB': 22, 'away_TO': 12},
        {'game_id': '2', 'date': '2025-11-05', 'season': 2026, 'neutral': 0, 'home_team': 'A', 'away_team': 'B',
         'home_score': 80, 'away_score': 50, 'home_FGA': 65, 'home_FGM': 30, 'home_3PA': 22, 'home_3PM': 9,
         'home_FTA': 21, 'home_ORB': 10, 'home_DRB': 25, 'home_TO': 11, 'away_FGA': 56, 'away_FGM': 20,
         'away_3PA': 17, 'away_3PM': 5, 'away_FTA': 14, 'away_ORB': 6, 'away_DRB': 21, 'away_TO': 13},
    ])
    games['date'] = pd.to_datetime(games['date'])
    games = add_four_factors(add_possessions(games))
    feats, _ = build_training_rows(games, half_life=35)
    assert len(feats) == 1
    assert feats.iloc[0]['game_id'] == '2'
