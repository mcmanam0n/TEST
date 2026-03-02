from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
from ncaam_sim.sim.game_sim import simulate_game


def simulate_bracket(checkpoint_dir: Path, team_state: pd.DataFrame, bracket_df: pd.DataFrame, sims: int, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    counts = defaultdict(lambda: defaultdict(int))
    for _ in range(sims):
        slots = {r.slot_id: {'teamA': r.teamA, 'teamB': r.teamB, 'round': r.round, 'next_slot_win': r.next_slot_win, 'next_slot_pos': r.next_slot_pos, 'neutral': int(r.neutral)}
                 for r in bracket_df.itertuples(index=False)}
        winners = {}
        for slot_id in sorted(slots, key=lambda x: int(str(x).split('_')[-1]) if '_' in str(x) else str(x)):
            s = slots[slot_id]
            if pd.isna(s['teamA']) or s['teamA'] == 'WINNER':
                continue
            res = simulate_game(checkpoint_dir, team_state, s['teamA'], s['teamB'], s['neutral'], sims=1, seed=int(rng.integers(1, 1_000_000)))
            w = s['teamA'] if res['win_rate_sim'] >= 0.5 else s['teamB']
            winners[slot_id] = w
            counts[w][f"round_{s['round']}"] += 1
            if pd.notna(s['next_slot_win']):
                ns = slots[s['next_slot_win']]
                ns['teamA' if s['next_slot_pos'] == 'A' else 'teamB'] = w
        if winners:
            champ = list(winners.values())[-1]
            counts[champ]['title'] += 1
    rows = []
    for team, d in counts.items():
        row = {'team': team}
        for k, v in d.items():
            row[k] = v / sims
        rows.append(row)
    return pd.DataFrame(rows).fillna(0)


def write_bracket_output(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
