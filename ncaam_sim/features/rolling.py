from __future__ import annotations
import math
from dataclasses import dataclass
import pandas as pd


@dataclass
class TeamSnapshot:
    metrics: dict[str, float]
    games_played: int


def recency_weight(days_ago: float, half_life: float) -> float:
    return math.exp(-math.log(2) * days_ago / half_life)


def team_long_format(games: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in games.iterrows():
        rows.append({'game_id': r['game_id'], 'date': r['date'], 'team': r['home_team'], 'opp': r['away_team'], 'is_home': 1,
                     'points': r['home_score'], 'opp_points': r['away_score'], 'OE': r['home_OE'], 'DE': r['home_DE'],
                     'tempo': r['tempo'], 'eFG_off': r['home_eFG'], 'eFG_def': r['away_eFG'], 'TO_off': r['home_TO_pct'],
                     'TO_def': r['away_TO_pct'], 'ORB_off': r['home_ORB_pct'], 'DRB_def': 1 - r['away_ORB_pct'],
                     'FTR_off': r['home_FTR'], 'FTR_def': r['away_FTR']})
        rows.append({'game_id': r['game_id'], 'date': r['date'], 'team': r['away_team'], 'opp': r['home_team'], 'is_home': 0,
                     'points': r['away_score'], 'opp_points': r['home_score'], 'OE': r['away_OE'], 'DE': r['away_DE'],
                     'tempo': r['tempo'], 'eFG_off': r['away_eFG'], 'eFG_def': r['home_eFG'], 'TO_off': r['away_TO_pct'],
                     'TO_def': r['home_TO_pct'], 'ORB_off': r['away_ORB_pct'], 'DRB_def': 1 - r['home_ORB_pct'],
                     'FTR_off': r['away_FTR'], 'FTR_def': r['home_FTR']})
    return pd.DataFrame(rows)


def snapshot_asof(team_games: pd.DataFrame, asof_date: pd.Timestamp, half_life: float, include_same_day: bool = False) -> TeamSnapshot:
    mask = team_games['date'] < asof_date if not include_same_day else team_games['date'] <= asof_date
    hist = team_games[mask]
    if hist.empty:
        return TeamSnapshot(metrics={}, games_played=0)
    days = (asof_date - hist['date']).dt.days.clip(lower=0)
    w = days.apply(lambda d: recency_weight(float(d), half_life))
    metrics = {}
    for c in ['OE', 'DE', 'tempo', 'eFG_off', 'eFG_def', 'TO_off', 'TO_def', 'ORB_off', 'DRB_def', 'FTR_off', 'FTR_def']:
        metrics[c] = float((hist[c] * w).sum() / w.sum())
    return TeamSnapshot(metrics=metrics, games_played=int(hist.shape[0]))
