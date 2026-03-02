# NCAAM 2025-26 As-of Simulator (Men's Pilot)

Reproducible CLI pipeline to ingest 2025-26 men's games, build no-leakage walk-forward features, fit win/margin models, calibrate probabilities, and simulate games or brackets.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Pretrain checkpoint

```bash
python scripts/run_pretrain_asof.py --asof 2026-03-01 --season_start 2025-11-01 --half_life 35 --ingest_source sportsdataverse
```

Fallback CSV ingestion:

```bash
python scripts/run_pretrain_asof.py --asof 2026-03-01 --ingest_source csv --csv_path data/raw/games_2025_2026.csv
```

Outputs:
- `data/raw/games_2025_2026.parquet`
- `data/processed/games_features.parquet`
- `data/processed/team_state_asof_<DATE>.parquet`
- `artifacts/checkpoints/<DATE>/...`

## Single game simulation

```bash
python scripts/run_game.py --asof 2026-03-01 --teamA "Duke" --teamB "Kansas" --neutral 1 --sims 20000 --seed 7
```

Writes `outputs/game_<TEAM_A>_vs_<TEAM_B>_<DATE>.json`.

## Bracket simulation

Bracket CSV schema:
- `slot_id, round, region, teamA, teamB, next_slot_win, next_slot_pos, neutral`

Use template at `data/brackets/2026_template.csv`.

```bash
python scripts/run_bracket.py --asof 2026-03-01 --bracket data/brackets/2026_template.csv --sims 100000 --seed 11
```

Writes `outputs/bracket_<DATE>.csv` (round reach and title odds).

## Data source notes

- Primary ingestion adapter: SportsDataverse (ESPN) wrapper module.
- If unavailable, CSV ingestion is supported.
- In this repository, SportsDataverse adapter gracefully falls back to a bundled synthetic sample to keep the pipeline executable in offline environments.

## Leakage policy

Training features for game at date `t` use only games strictly before `t`. Team-state export at `--asof` uses games `<= asof`.

## Smoke test

```bash
pytest -q
python scripts/run_pretrain_asof.py --asof 2026-03-01
python scripts/run_game.py --asof 2026-03-01 --teamA "Duke" --teamB "Kansas" --neutral 1 --sims 5000
```

## Known limitations

- SportsDataverse adapter includes placeholder endpoint handling and currently uses synthetic fallback when endpoint mapping/import fails.
- Bracket engine assumes slot graph provided via `next_slot_win` pointers.
- Margin uncertainty uses tempo-binned residual std (simple, fast heuristic).
