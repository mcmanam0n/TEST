import pandas as pd


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    return a / b.replace(0, pd.NA)


def add_four_factors(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['home_eFG'] = _safe_div(out['home_FGM'] + 0.5 * out['home_3PM'], out['home_FGA'])
    out['away_eFG'] = _safe_div(out['away_FGM'] + 0.5 * out['away_3PM'], out['away_FGA'])
    out['home_TO_pct'] = _safe_div(out['home_TO'], out['poss'])
    out['away_TO_pct'] = _safe_div(out['away_TO'], out['poss'])
    out['home_ORB_pct'] = _safe_div(out.get('home_ORB', 0), out.get('home_ORB', 0) + out.get('away_DRB', 1))
    out['away_ORB_pct'] = _safe_div(out.get('away_ORB', 0), out.get('away_ORB', 0) + out.get('home_DRB', 1))
    out['home_FTR'] = _safe_div(out['home_FTA'], out['home_FGA'])
    out['away_FTR'] = _safe_div(out['away_FTA'], out['away_FGA'])
    out['home_OE'] = 100 * _safe_div(out['home_score'], out['poss'])
    out['away_OE'] = 100 * _safe_div(out['away_score'], out['poss'])
    out['home_DE'] = out['away_OE']
    out['away_DE'] = out['home_OE']
    out['tempo'] = out['poss']
    return out.fillna(0)
