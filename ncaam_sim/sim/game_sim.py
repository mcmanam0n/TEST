from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import json
from ncaam_sim.features.matchup import FEATURE_COLUMNS, build_matchup_features
from ncaam_sim.utils.io import write_json


def _sigma_for_tempo(expected_tempo: float, tempo_bins: list[float], stds: list[float]) -> float:
    idx = np.digitize([expected_tempo], tempo_bins[1:-1], right=False)[0]
    return float(stds[idx])


def simulate_game(checkpoint_dir: Path, team_state: pd.DataFrame, teamA: str, teamB: str, neutral: int, sims: int, seed: int = 7) -> dict:
    win_model = joblib.load(checkpoint_dir / 'win_model.pkl')
    margin_model = joblib.load(checkpoint_dir / 'margin_model.pkl')
    calibrator = joblib.load(checkpoint_dir / 'calibrator.pkl')
    scaler = joblib.load(checkpoint_dir / 'scaler.pkl')
    with (checkpoint_dir / 'config.json').open('r', encoding='utf-8') as f:
        config = json.load(f)
    rowA = team_state[team_state['team'] == teamA].iloc[0]
    rowB = team_state[team_state['team'] == teamB].iloc[0]
    feats = build_matchup_features(rowA, rowB, neutral)
    X = pd.DataFrame([feats])[FEATURE_COLUMNS]
    Xs = scaler.transform(X)
    p_raw = win_model.predict_proba(Xs)[:, 1][0]
    p = float(calibrator.predict([p_raw])[0])
    mu = float(margin_model.predict(Xs)[0])
    sigma = _sigma_for_tempo(feats['expected_tempo'], config['tempo_bins'], config['tempo_stds'])
    rng = np.random.default_rng(seed)
    margins = rng.normal(mu, sigma, size=sims)
    league_ppp = config.get('league_avg_ppp', 1.02)
    total = feats['expected_tempo'] * league_ppp
    scoresA = np.clip((total + margins) / 2, 45, 120)
    scoresB = np.clip((total - margins) / 2, 45, 120)
    out = {
        'teamA': teamA, 'teamB': teamB, 'p_teamA_win_calibrated': p, 'mu_margin': mu, 'sigma_margin': sigma,
        'win_rate_sim': float((margins > 0).mean()), 'p10_margin': float(np.percentile(margins, 10)),
        'p50_margin': float(np.percentile(margins, 50)), 'p90_margin': float(np.percentile(margins, 90)),
        'exp_scoreA': float(scoresA.mean()), 'exp_scoreB': float(scoresB.mean())
    }
    return out


def write_game_output(out: dict, path: Path) -> None:
    write_json(path, out)
