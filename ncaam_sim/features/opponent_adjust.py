import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge


def fit_strength_ratings(team_games: pd.DataFrame, asof_date: pd.Timestamp, half_life: float, alpha: float = 5.0) -> pd.DataFrame:
    teams = sorted(team_games['team'].unique())
    idx = {t: i for i, t in enumerate(teams)}
    subset = team_games[team_games['date'] <= asof_date].copy()
    n = len(subset)
    X = np.zeros((n, len(teams) * 2))
    y = subset['OE'].to_numpy()
    days = (asof_date - subset['date']).dt.days.clip(lower=0).to_numpy()
    w = np.exp(-np.log(2) * days / half_life)
    for r, row in enumerate(subset.itertuples(index=False)):
        X[r, idx[row.team]] = 1.0
        X[r, len(teams) + idx[row.opp]] = -1.0
    model = Ridge(alpha=alpha, fit_intercept=True)
    model.fit(X, y, sample_weight=w)
    coef = model.coef_
    off = coef[:len(teams)]
    deff = coef[len(teams):]
    off = off - off.mean()
    deff = deff - deff.mean()
    return pd.DataFrame({'team': teams, 'OffStr': off, 'DefStr': deff})
