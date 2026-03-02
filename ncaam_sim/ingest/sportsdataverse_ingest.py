import numpy as np
import pandas as pd
from ncaam_sim.ingest.base import Ingestor
from ncaam_sim.utils.logging import get_logger

logger = get_logger(__name__)


class SportsDataverseIngestor(Ingestor):
    def fetch_games(self, season_start: str, asof: str) -> pd.DataFrame:
        try:
            import sportsdataverse as sdv  # type: ignore
            _ = sdv
            raise RuntimeError('sportsdataverse adapter placeholder: endpoint mapping may vary by environment')
        except Exception as exc:
            logger.warning('SportsDataverse fetch unavailable (%s). Falling back to bundled synthetic sample.', exc)
            return self._synthetic_games(season_start, asof)

    def _synthetic_games(self, season_start: str, asof: str) -> pd.DataFrame:
        teams = ['Duke', 'Kansas', 'UConn', 'Houston', 'Purdue', 'Arizona', 'Baylor', 'Gonzaga']
        rng = np.random.default_rng(42)
        dates = pd.date_range(season_start, asof, freq='3D')
        rows = []
        gid = 1
        for d in dates:
            a, b = rng.choice(teams, size=2, replace=False)
            hs = int(rng.normal(75, 10))
            aw = int(rng.normal(72, 10))
            rows.append({
                'game_id': f'g{gid}', 'date': d, 'season': 2026, 'neutral': int(rng.random() < 0.2),
                'home_team': a, 'away_team': b, 'home_score': hs, 'away_score': aw,
                'home_FGA': int(rng.integers(50, 70)), 'home_FGM': int(rng.integers(20, 35)),
                'home_3PA': int(rng.integers(15, 30)), 'home_3PM': int(rng.integers(5, 13)),
                'home_FTA': int(rng.integers(10, 25)), 'home_ORB': int(rng.integers(6, 16)),
                'home_DRB': int(rng.integers(18, 30)), 'home_TO': int(rng.integers(8, 18)),
                'away_FGA': int(rng.integers(50, 70)), 'away_FGM': int(rng.integers(20, 35)),
                'away_3PA': int(rng.integers(15, 30)), 'away_3PM': int(rng.integers(5, 13)),
                'away_FTA': int(rng.integers(10, 25)), 'away_ORB': int(rng.integers(6, 16)),
                'away_DRB': int(rng.integers(18, 30)), 'away_TO': int(rng.integers(8, 18)),
            })
            gid += 1
        return pd.DataFrame(rows)
