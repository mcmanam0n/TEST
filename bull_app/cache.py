from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf


DATA_COLS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def _cache_path(cache_dir: Path, ticker: str, start_date: str) -> Path:
    safe_ticker = ticker.replace("^", "_")
    return cache_dir / f"{safe_ticker}_{start_date}_1d.csv"


def _is_fresh(path: Path, max_age_hours: int = 12) -> bool:
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age <= timedelta(hours=max_age_hours)


def _clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    cleaned = df.copy()
    if isinstance(cleaned.columns, pd.MultiIndex):
        cleaned.columns = [c[0] for c in cleaned.columns]

    cleaned = cleaned.reset_index()
    if "Date" not in cleaned.columns:
        if "index" in cleaned.columns:
            cleaned = cleaned.rename(columns={"index": "Date"})
        else:
            cleaned.columns = ["Date", *cleaned.columns[1:]]

    for col in DATA_COLS:
        if col not in cleaned.columns:
            cleaned[col] = pd.NA

    cleaned = cleaned[["Date", *DATA_COLS]]
    cleaned["Date"] = pd.to_datetime(cleaned["Date"])
    cleaned = cleaned.sort_values("Date").dropna().set_index("Date")
    return cleaned


def load_or_download_ticker(ticker: str, start_date: str, cache_dir: Path) -> pd.DataFrame:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_dir, ticker, start_date)

    if _is_fresh(path):
        cached = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
        return _clean_ohlcv(cached)

    downloaded = yf.download(
        ticker,
        start=start_date,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    cleaned = _clean_ohlcv(downloaded)
    if cleaned.empty:
        return cleaned

    cleaned.to_csv(path)
    return cleaned
