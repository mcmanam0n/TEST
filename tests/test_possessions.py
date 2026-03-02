import pandas as pd
from ncaam_sim.features.possessions import add_possessions


def test_possessions_formula():
    df = pd.DataFrame([{
        'home_FGA': 60, 'home_ORB': 10, 'home_TO': 12, 'home_FTA': 20,
        'away_FGA': 58, 'away_ORB': 8, 'away_TO': 11, 'away_FTA': 18
    }])
    out = add_possessions(df)
    expected = 0.5 * ((60 - 10 + 12 + 0.475 * 20) + (58 - 8 + 11 + 0.475 * 18))
    assert abs(out.loc[0, 'poss'] - expected) < 1e-9
