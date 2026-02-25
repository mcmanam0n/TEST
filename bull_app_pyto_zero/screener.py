import csv
import io
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

from indicators import (
    atr,
    atr_contraction_breakout,
    golden_cross_recent,
    macd,
    rsi_wilder,
    rs_up,
    sma,
)
from scoring import build_reasons, score_row, strict_pass
from storage import CACHE_DIR, RESULTS_FILE, SKIPPED_FILE, write_csv
from universe import load_universe


CACHE_TTL = 24 * 60 * 60
NETWORK_TIMEOUT_S = 6
MAX_WORKERS = 8
MIN_ROWS = 220


def default_start_date():
    return (date.today() - timedelta(days=365 * 3)).isoformat()


def to_stooq_symbol(ticker: str) -> str:
    return ticker.strip().lower().replace(".", "-") + ".us"


def _cache_path(ticker, start):
    safe_start = start.replace("-", "")
    return os.path.join(CACHE_DIR, f"{ticker.upper()}_{safe_start}.csv")


def _fetch_stooq_csv(symbol):
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    with urllib.request.urlopen(url, timeout=NETWORK_TIMEOUT_S) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_price_rows(ticker, start):
    path = _cache_path(ticker, start)
    use_cache = os.path.exists(path) and (time.time() - os.path.getmtime(path) <= CACHE_TTL)
    if use_cache:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    else:
        content = _fetch_stooq_csv(to_stooq_symbol(ticker))
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    rows = []
    reader = csv.DictReader(io.StringIO(content))
    for r in reader:
        d = r.get("Date", "")
        if not d or d < start:
            continue
        try:
            rows.append(
                {
                    "date": d,
                    "open": float(r["Open"]),
                    "high": float(r["High"]),
                    "low": float(r["Low"]),
                    "close": float(r["Close"]),
                    "volume": float(r.get("Volume", 0) or 0),
                }
            )
        except Exception:
            continue
    return rows


def _compute_metrics(rows, spy_rows=None):
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]

    sma50 = sma(closes, 50)
    sma200 = sma(closes, 200)
    rsi14 = rsi_wilder(closes, 14)
    rsi_avg10 = sma([x if x is not None else 50.0 for x in rsi14], 10)
    macd_line, signal, hist = macd(closes)
    atr14 = atr(highs, lows, closes, 14)
    atr_pct = [None if atr14[i] is None else atr14[i] / closes[i] for i in range(len(closes))]

    rs_ok = False
    if spy_rows:
        spy_map = {r["date"]: r["close"] for r in spy_rows}
        rs_series = []
        for r in rows:
            s = spy_map.get(r["date"])
            if s:
                rs_series.append(r["close"] / s)
        if len(rs_series) >= 60:
            rs_ok = rs_up(rs_series)

    hist_rising = len(hist) >= 6 and all(
        hist[-i] is not None and hist[-i - 1] is not None and hist[-i] > hist[-i - 1]
        for i in range(1, 6)
    )

    flags = {
        "golden_cross_recent": golden_cross_recent(sma50, sma200, 60),
        "price_above_200": sma200[-1] is not None and closes[-1] > sma200[-1],
        "sma200_up": len(sma200) > 20 and sma200[-1] is not None and sma200[-21] is not None and sma200[-1] > sma200[-21],
        "rsi_regime": rsi14[-1] is not None and rsi14[-1] > 50 and rsi_avg10[-1] is not None and len(rsi_avg10) > 6 and rsi_avg10[-1] > rsi_avg10[-6],
        "macd_bullish": macd_line[-1] is not None and signal[-1] is not None and macd_line[-1] > signal[-1] and hist_rising,
        "atr_contraction_breakout": atr_contraction_breakout(atr_pct, closes, highs),
        "rs_up": rs_ok,
        "close_60d_high": len(closes) > 60 and closes[-1] >= max(closes[-60:]),
        "ret20_positive": len(closes) > 20 and closes[-1] > closes[-21],
        "sma50_over_sma200": sma50[-1] is not None and sma200[-1] is not None and sma50[-1] > sma200[-1],
        "close_over_sma50": sma50[-1] is not None and closes[-1] > sma50[-1],
    }

    return {
        "price": closes[-1],
        "sma50": sma50[-1],
        "sma200": sma200[-1],
        "rsi14": rsi14[-1],
        "macd": macd_line[-1],
        "macd_signal": signal[-1],
        "macd_hist": hist[-1],
        "atr_pct": atr_pct[-1],
        "flags": flags,
    }


def _screen_one(ticker, start_date, spy_rows, spy_failed, strict_mode):
    rows = get_price_rows(ticker, start_date)
    if len(rows) < MIN_ROWS:
        return None, {"ticker": ticker, "reason": "too few rows"}

    metrics = _compute_metrics(rows, spy_rows)
    flags = metrics["flags"]
    score = score_row(flags)
    reasons = build_reasons(flags)

    if spy_failed:
        reasons = (reasons + "; rs limited: SPY unavailable").strip("; ")
    if strict_mode and not strict_pass(flags):
        return None, None

    result = {
        "ticker": ticker,
        "score": score,
        "price": f"{metrics['price']:.2f}",
        "sma50": f"{metrics['sma50']:.2f}" if metrics["sma50"] is not None else "",
        "sma200": f"{metrics['sma200']:.2f}" if metrics["sma200"] is not None else "",
        "golden_cross_recent": str(flags["golden_cross_recent"]),
        "price_above_200": str(flags["price_above_200"]),
        "sma200_up": str(flags["sma200_up"]),
        "rsi14": f"{metrics['rsi14']:.2f}" if metrics["rsi14"] is not None else "",
        "rsi_regime": str(flags["rsi_regime"]),
        "macd": f"{metrics['macd']:.4f}" if metrics["macd"] is not None else "",
        "macd_signal": f"{metrics['macd_signal']:.4f}" if metrics["macd_signal"] is not None else "",
        "macd_hist": f"{metrics['macd_hist']:.4f}" if metrics["macd_hist"] is not None else "",
        "macd_bullish": str(flags["macd_bullish"]),
        "atr_pct": f"{metrics['atr_pct']:.4f}" if metrics["atr_pct"] is not None else "",
        "atr_contraction_breakout": str(flags["atr_contraction_breakout"]),
        "rs_up": str(flags["rs_up"]),
        "reasons": reasons,
    }
    return result, None


def run_screener(start_date=None, top_n=25, strict_mode=False, include_macro=False):
    start_date = start_date or default_start_date()
    tickers = load_universe()
    results = []
    skipped = []

    spy_rows = None
    spy_failed = False
    try:
        spy_rows = get_price_rows("SPY", start_date)
        if len(spy_rows) < MIN_ROWS:
            spy_failed = True
            spy_rows = None
    except Exception as e:
        spy_failed = True
        skipped.append({"ticker": "SPY", "reason": f"spy fetch failed: {e}"})

    workers = min(MAX_WORKERS, max(1, len(tickers)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_screen_one, t, start_date, spy_rows, spy_failed, strict_mode): t
            for t in tickers
        }
        for fut in as_completed(futures):
            ticker = futures[fut]
            try:
                result, skip = fut.result()
                if result:
                    results.append(result)
                if skip:
                    skipped.append(skip)
            except Exception as e:
                skipped.append({"ticker": ticker, "reason": str(e)[:140]})

    results.sort(key=lambda x: int(x["score"]), reverse=True)
    try:
        top_n_int = max(1, int(top_n))
    except Exception:
        top_n_int = 25
    results = results[:top_n_int]

    result_fields = [
        "ticker", "score", "price", "sma50", "sma200", "golden_cross_recent", "price_above_200", "sma200_up",
        "rsi14", "rsi_regime", "macd", "macd_signal", "macd_hist", "macd_bullish", "atr_pct", "atr_contraction_breakout", "rs_up", "reasons",
    ]
    write_csv(RESULTS_FILE, result_fields, results)
    write_csv(SKIPPED_FILE, ["ticker", "reason"], skipped)
    return len(results), len(skipped)
