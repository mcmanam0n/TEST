import pandas as pd
from ncaam_sim.features.rolling import team_long_format, snapshot_asof
from ncaam_sim.features.opponent_adjust import fit_strength_ratings
from ncaam_sim.features.matchup import build_matchup_features


def build_training_rows(games: pd.DataFrame, half_life: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    games = games.sort_values('date').reset_index(drop=True)
    tl = team_long_format(games)
    rows = []
    for g in games.itertuples(index=False):
        game_date = pd.to_datetime(g.date)
        rating_df = fit_strength_ratings(tl, game_date - pd.Timedelta(days=1), half_life)
        snap = {}
        for t in [g.home_team, g.away_team]:
            sg = tl[tl['team'] == t]
            s = snapshot_asof(sg, game_date, half_life, include_same_day=False)
            if s.games_played == 0:
                continue
            s.metrics['games_played'] = s.games_played
            snap[t] = s.metrics
        if g.home_team not in snap or g.away_team not in snap:
            continue
        rA = rating_df[rating_df['team'] == g.home_team]
        rB = rating_df[rating_df['team'] == g.away_team]
        if rA.empty or rB.empty:
            continue
        snap[g.home_team]['OffStr'] = float(rA['OffStr'].iloc[0])
        snap[g.home_team]['DefStr'] = float(rA['DefStr'].iloc[0])
        snap[g.away_team]['OffStr'] = float(rB['OffStr'].iloc[0])
        snap[g.away_team]['DefStr'] = float(rB['DefStr'].iloc[0])
        feats = build_matchup_features(pd.Series(snap[g.home_team]), pd.Series(snap[g.away_team]), int(g.neutral))
        feats.update({'game_id': g.game_id, 'date': g.date, 'teamA': g.home_team, 'teamB': g.away_team,
                      'win': int(g.home_score > g.away_score), 'margin': g.home_score - g.away_score})
        rows.append(feats)
    train = pd.DataFrame(rows)
    return train, tl


def build_team_state_asof(tl: pd.DataFrame, asof_date: str, half_life: float) -> pd.DataFrame:
    asof_ts = pd.to_datetime(asof_date)
    ratings = fit_strength_ratings(tl, asof_ts, half_life)
    rows = []
    for team in sorted(tl['team'].unique()):
        s = snapshot_asof(tl[tl['team'] == team], asof_ts, half_life, include_same_day=True)
        if s.games_played == 0:
            continue
        out = {'team': team, **s.metrics, 'games_played': s.games_played}
        r = ratings[ratings['team'] == team].iloc[0]
        out['OffStr'] = float(r['OffStr'])
        out['DefStr'] = float(r['DefStr'])
        rows.append(out)
    return pd.DataFrame(rows)
