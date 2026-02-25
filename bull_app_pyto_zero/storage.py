import csv
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
STATIC_DIR = os.path.join(BASE_DIR, "static")
RESULTS_FILE = os.path.join(DATA_DIR, "results.csv")
SKIPPED_FILE = os.path.join(DATA_DIR, "skipped.csv")


def ensure_dirs():
    for p in (DATA_DIR, CACHE_DIR, STATIC_DIR):
        os.makedirs(p, exist_ok=True)


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def last_run_time(path=RESULTS_FILE):
    if not os.path.exists(path):
        return "Never"
    ts = datetime.fromtimestamp(os.path.getmtime(path))
    return ts.strftime("%Y-%m-%d %H:%M:%S")
