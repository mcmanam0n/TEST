#!/usr/bin/env python
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from ncaam_sim.config import DEFAULT_ASOF, DEFAULT_HALF_LIFE_DAYS, DEFAULT_SEASON_START, Paths
from ncaam_sim.features.possessions import add_possessions
from ncaam_sim.features.four_factors import add_four_factors
from ncaam_sim.features.dataset_builder import build_training_rows, build_team_state_asof
from ncaam_sim.features.matchup import FEATURE_COLUMNS
from ncaam_sim.ingest.csv_ingest import CSVIngestor
from ncaam_sim.ingest.sportsdataverse_ingest import SportsDataverseIngestor
from ncaam_sim.models.train_win import train_win_model
from ncaam_sim.models.train_margin import train_margin_model
from ncaam_sim.models.calibrate import fit_calibrator
from ncaam_sim.models.evaluate import compute_metrics
from ncaam_sim.models.artifacts import save_artifacts
from ncaam_sim.utils.io import write_table
from ncaam_sim.utils.team_ids import canonicalize_team, load_alias_overrides


def parse_args():
    p = argparse.ArgumentParser(description='Pretrain NCAAM simulator checkpoint as-of date.')
    p.add_argument('--asof', default=DEFAULT_ASOF)
    p.add_argument('--season_start', default=DEFAULT_SEASON_START)
    p.add_argument('--half_life', type=float, default=DEFAULT_HALF_LIFE_DAYS)
    p.add_argument('--ingest_source', choices=['sportsdataverse', 'csv'], default='sportsdataverse')
    p.add_argument('--csv_path', default='')
    return p.parse_args()


def main():
    args = parse_args()
    paths = Paths()
    if args.ingest_source == 'csv':
        ing = CSVIngestor(args.csv_path)
    else:
        ing = SportsDataverseIngestor()
    games = ing.fetch_games(args.season_start, args.asof)
    aliases = {**load_alias_overrides(),}
    games['home_team'] = games['home_team'].map(lambda x: canonicalize_team(str(x), aliases))
    games['away_team'] = games['away_team'].map(lambda x: canonicalize_team(str(x), aliases))
    games['date'] = pd.to_datetime(games['date'])
    games = add_four_factors(add_possessions(games))

    raw_path = paths.raw / 'games_2025_2026.parquet'
    write_table(games, raw_path)

    train_df, tl = build_training_rows(games, args.half_life)
    if train_df.empty:
        raise RuntimeError('No training rows created; ensure enough historical games before as-of date.')
    write_table(train_df, paths.processed / 'games_features.parquet')

    team_state = build_team_state_asof(tl, args.asof, args.half_life)
    write_table(team_state, paths.processed / f'team_state_asof_{args.asof}.parquet')

    split_date = train_df.sort_values('date')['date'].iloc[int(len(train_df) * 0.8)]
    tr = train_df[train_df['date'] < split_date]
    va = train_df[train_df['date'] >= split_date]
    if tr.empty or va.empty:
        tr = train_df.iloc[:-1].copy()
        va = train_df.iloc[-1:].copy()

    scaler = StandardScaler()
    Xtr = scaler.fit_transform(tr[FEATURE_COLUMNS])
    Xva = scaler.transform(va[FEATURE_COLUMNS])
    win = train_win_model(pd.DataFrame(Xtr), tr['win'])
    margin = train_margin_model(pd.DataFrame(Xtr), tr['margin'])

    p_raw_va = win.predict_proba(Xva)[:, 1]
    calibrator = fit_calibrator(p_raw_va, va['win'].to_numpy())
    p_cal_va = calibrator.predict(p_raw_va)
    mu_va = margin.predict(Xva)

    qbins = np.quantile(train_df['expected_tempo'], [0.0, 0.33, 0.66, 1.0])
    mu_tr = margin.predict(Xtr)
    resid = tr['margin'].to_numpy() - mu_tr
    bin_id = np.digitize(tr['expected_tempo'], qbins[1:-1], right=False)
    stds = [float(np.std(resid[bin_id == i]) if np.any(bin_id == i) else np.std(resid)) for i in range(3)]

    metrics = compute_metrics(va['win'].to_numpy(), p_cal_va, va['margin'].to_numpy(), mu_va)
    metrics['poss_proxy_rate'] = float(games['poss_proxy_used'].mean())
    metrics['n_games_raw'] = int(len(games))
    metrics['n_rows_train'] = int(len(train_df))

    config = {
        'feature_columns': FEATURE_COLUMNS,
        'half_life_days': args.half_life,
        'possessions_formula': '0.5*((FGA-ORB+TO+0.475*FTA)_A + (FGA-ORB+TO+0.475*FTA)_B)',
        'tempo_bins': list(map(float, qbins)),
        'tempo_stds': stds,
        'league_avg_ppp': float((games['home_score'].sum() + games['away_score'].sum()) / (2 * games['poss'].sum())),
        'asof': args.asof,
    }

    ckpt = paths.artifacts / args.asof
    save_artifacts(ckpt, win, margin, calibrator, scaler, config, metrics)
    print(f'Saved checkpoint to {ckpt}')


if __name__ == '__main__':
    main()
