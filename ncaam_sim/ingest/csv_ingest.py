from pathlib import Path
import pandas as pd
from ncaam_sim.ingest.base import Ingestor


class CSVIngestor(Ingestor):
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)

    def fetch_games(self, season_start: str, asof: str) -> pd.DataFrame:
        if not self.csv_path.exists():
            raise FileNotFoundError(f'CSV not found: {self.csv_path}')
        df = pd.read_csv(self.csv_path)
        df['date'] = pd.to_datetime(df['date'])
        return df[(df['date'] >= pd.to_datetime(season_start)) & (df['date'] <= pd.to_datetime(asof))].copy()
