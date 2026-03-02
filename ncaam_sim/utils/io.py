import json
from pathlib import Path
import pandas as pd


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    ensure_dir(path.parent)
    with path.open('w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix == '.parquet':
        return pd.read_parquet(path)
    return pd.read_csv(path)


def write_table(df: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    if path.suffix == '.parquet':
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)
