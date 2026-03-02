#!/usr/bin/env python
import argparse
import pandas as pd
from ncaam_sim.config import Paths
from ncaam_sim.sim.bracket_sim import simulate_bracket, write_bracket_output


def parse_args():
    p = argparse.ArgumentParser(description='Monte Carlo simulation for bracket slots.')
    p.add_argument('--asof', required=True)
    p.add_argument('--bracket', required=True)
    p.add_argument('--sims', type=int, default=100000)
    p.add_argument('--seed', type=int, default=11)
    return p.parse_args()


def main():
    args = parse_args()
    req = {'slot_id', 'round', 'region', 'teamA', 'teamB', 'next_slot_win', 'next_slot_pos', 'neutral'}
    bracket = pd.read_csv(args.bracket)
    missing = req - set(bracket.columns)
    if missing:
        raise ValueError(f'Missing bracket columns: {sorted(missing)}')
    paths = Paths()
    checkpoint = paths.artifacts / args.asof
    team_state = pd.read_parquet(paths.processed / f'team_state_asof_{args.asof}.parquet')
    out = simulate_bracket(checkpoint, team_state, bracket, args.sims, args.seed)
    write_bracket_output(out, paths.outputs / f'bracket_{args.asof}.csv')
    print(out.head())


if __name__ == '__main__':
    main()
