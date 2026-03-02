from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    root: Path = Path('.')
    raw: Path = Path('data/raw')
    processed: Path = Path('data/processed')
    artifacts: Path = Path('artifacts/checkpoints')
    outputs: Path = Path('outputs')


DEFAULT_HALF_LIFE_DAYS = 35.0
DEFAULT_SEASON_START = '2025-11-01'
DEFAULT_ASOF = '2026-03-01'
LEAGUE_AVG_PPP_FALLBACK = 1.02
