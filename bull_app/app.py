"""
README (Pyto iPhone quick start)
1) In Pyto, install dependencies once:
   pip install flask pandas numpy yfinance
2) Copy this bull_app folder into Pyto's files area.
3) In Pyto terminal/editor, cd into bull_app and run:
   python app.py
4) Keep Pyto running and open Safari on iPhone to:
   http://127.0.0.1:5000
5) Run a scan from the form, then view/download CSV results.
"""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from flask import Flask, redirect, render_template, request, send_file, url_for

from screener import run_screener
from universe import load_tickers

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
RESULTS_CSV = DATA_DIR / "results.csv"
SKIPPED_CSV = DATA_DIR / "skipped.csv"

app = Flask(__name__)


@app.get("/")
def index():
    default_start = (date.today() - timedelta(days=365 * 3)).isoformat()
    return render_template("index.html", default_start=default_start)


@app.post("/run")
def run():
    universe = request.form.get("universe", "custom")
    custom_tickers = request.form.get("tickers", "")
    start_date = request.form.get("start_date") or (date.today() - timedelta(days=365 * 3)).isoformat()
    top_n = int(request.form.get("top_n", 25))
    macro_enabled = request.form.get("macro_enabled") == "on"

    tickers = load_tickers(universe, custom_tickers, BASE_DIR)
    if not tickers:
        pd.DataFrame(columns=["ticker", "reason"]).to_csv(SKIPPED_CSV, index=False)
        pd.DataFrame().to_csv(RESULTS_CSV, index=False)
        return redirect(url_for("results", top_n=top_n))

    results_df, _ = run_screener(
        tickers=tickers,
        start_date=start_date,
        cache_dir=CACHE_DIR,
        results_path=RESULTS_CSV,
        skipped_path=SKIPPED_CSV,
        macro_enabled=macro_enabled,
    )

    if not results_df.empty:
        results_df.head(top_n).to_csv(RESULTS_CSV, index=False)

    return redirect(url_for("results"))


@app.get("/results")
def results():
    results_df = pd.read_csv(RESULTS_CSV) if RESULTS_CSV.exists() else pd.DataFrame()
    skipped_df = pd.read_csv(SKIPPED_CSV) if SKIPPED_CSV.exists() else pd.DataFrame()

    results_records = results_df.to_dict(orient="records") if not results_df.empty else []
    skipped_records = skipped_df.to_dict(orient="records") if not skipped_df.empty else []

    return render_template(
        "results.html",
        results=results_records,
        skipped=skipped_records,
        columns=list(results_df.columns),
    )


@app.get("/download/results.csv")
def download_results():
    return send_file(RESULTS_CSV, as_attachment=True)


@app.get("/download/skipped.csv")
def download_skipped():
    return send_file(SKIPPED_CSV, as_attachment=True)


if __name__ == "__main__":
    print("Bull app running at: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
