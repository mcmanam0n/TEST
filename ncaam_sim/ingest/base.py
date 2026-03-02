from abc import ABC, abstractmethod
import pandas as pd


class Ingestor(ABC):
    @abstractmethod
    def fetch_games(self, season_start: str, asof: str) -> pd.DataFrame:
        ...
