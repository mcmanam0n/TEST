import numpy as np
import pandas as pd


def estimate_possessions(fga: pd.Series, orb: pd.Series, tov: pd.Series, fta: pd.Series) -> pd.Series:
    return fga - orb + tov + 0.475 * fta


def add_possessions(df: pd.DataFrame) -> pd.DataFrame:
    h = estimate_possessions(df['home_FGA'], df.get('home_ORB', 0), df['home_TO'], df['home_FTA'])
    a = estimate_possessions(df['away_FGA'], df.get('away_ORB', 0), df['away_TO'], df['away_FTA'])
    df = df.copy()
    df['poss'] = 0.5 * (h + a)
    df['poss_proxy_used'] = np.where(df['poss'] <= 0, 1, 0)
    df.loc[df['poss'] <= 0, 'poss'] = 68.0
    return df
