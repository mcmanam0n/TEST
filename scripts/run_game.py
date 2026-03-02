#!/usr/bin/env python
import argparse
from pathlib import Path
import pandas as pd
from ncaam_sim.config import Paths
from ncaam_sim.sim.game_sim import simulate_game, write_game_output


def parse_args():
    p = argparse.ArgumentParser(description='Simulate a single NCAAM matchup using pretrained checkpoint.')
    p.add_argument('--asof', required=True)
    p.add_argument('--teamA', required=True)
    p.add_argument('--teamB', required=True)
    p.add_argument('--neutral', type=int, default=1)
    p.add_argument('--sims', type=int, default=20000)
    p.add_argument('--seed', type=int, default=7)
    return p.parse_args()


def main():
    args = parse_args()
    paths = Paths()
    checkpoint = paths.artifacts / args.asof
    team_state = pd.read_parquet(paths.processed / f'team_state_asof_{args.asof}.parquet')
    out = simulate_game(checkpoint, team_state, args.teamA, args.teamB, args.neutral, args.sims, args.seed)
    out_path = paths.outputs / f'game_{args.teamA}_vs_{args.teamB}_{args.asof}.json'
    write_game_output(out, out_path)
    print(out)


if __name__ == '__main__':
    main()
