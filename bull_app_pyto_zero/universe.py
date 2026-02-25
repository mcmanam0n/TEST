import csv
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UNIVERSE_FILE = os.path.join(BASE_DIR, "data", "nasdaq100.csv")


def load_universe(path=UNIVERSE_FILE):
    tickers = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = (row.get("ticker") or "").strip().upper()
            if t:
                tickers.append(t)
    return tickers
