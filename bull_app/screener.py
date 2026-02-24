from __future__ import annotations

from pathlib import Path

import pandas as pd

from cache import load_or_download_ticker
from indicators import atr, macd, rsi_wilder, sma
from scoring import compute_score


def _latest(series: pd.Series):
    return float(series.iloc[-1]) if not series.empty else float("nan")


def _macro_status(start_date: str, cache_dir: Path) -> tuple[bool, dict]:
    details = {"spy_ok": False, "vix_ok": False, "tnx_ok": False}

    spy = load_or_download_ticker("SPY", start_date, cache_dir)
    vix = load_or_download_ticker("^VIX", start_date, cache_dir)
    tnx = load_or_download_ticker("^TNX", start_date, cache_dir)

    if len(spy) >= 220:
        spy_close = spy["Close"]
        spy_sma200 = sma(spy_close, 200)
        details["spy_ok"] = bool(spy_close.iloc[-1] > spy_sma200.iloc[-1] and spy_sma200.iloc[-1] > spy_sma200.iloc[-20])

    if len(vix) >= 60:
        vix_sma50 = sma(vix["Close"], 50)
        details["vix_ok"] = bool(vix["Close"].iloc[-1] < vix_sma50.iloc[-1])

    if len(tnx) >= 40:
        details["tnx_ok"] = bool((tnx["Close"].iloc[-1] - tnx["Close"].iloc[-20]) <= 0)

    return all(details.values()), details


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    out = df.copy()
    out["sma50"] = sma(close, 50)
    out["sma200"] = sma(close, 200)
    out["rsi14"] = rsi_wilder(close, 14)

    macd_line, signal, hist = macd(close)
    out["macd"] = macd_line
    out["macd_signal"] = signal
    out["macd_hist"] = hist

    out["atr14"] = atr(high, low, close, 14)
    out["atr_pct"] = out["atr14"] / close
    out["prior20_high"] = high.shift(1).rolling(20, min_periods=20).max()
    out["high60"] = close.rolling(60, min_periods=60).max()
    out["ret20"] = close.pct_change(20)

    return out


def _calc_metrics(ticker_df: pd.DataFrame, spy_df: pd.DataFrame, macro_ok: bool, macro_enabled: bool) -> dict:
    df = _enrich(ticker_df)
    if len(df) < 220:
        raise ValueError("insufficient history (<220 rows)")

    latest = df.iloc[-1]
    sma50 = df["sma50"]
    sma200 = df["sma200"]

    cross_window = 60
    cross = (sma50 > sma200) & (sma50.shift(1) <= sma200.shift(1))
    golden_cross_recent = bool(cross.tail(cross_window).any())

    price_above_200 = bool(latest["Close"] > latest["sma200"])
    sma200_up = bool(sma200.iloc[-1] > sma200.iloc[-20])

    rsi_val = float(latest["rsi14"])
    rsi_regime = bool(rsi_val >= 50)

    macd_bullish = bool(
        latest["macd"] > latest["macd_signal"]
        and (df["macd_hist"].diff().tail(5).dropna() > 0).all()
    )

    atr_contraction_breakout = bool(
        latest["atr_pct"] < df["atr_pct"].tail(60).median()
        and latest["Close"] > latest["prior20_high"]
    )

    spy_aligned = spy_df.reindex(df.index).dropna()
    rs = (df.loc[spy_aligned.index, "Close"] / spy_aligned["Close"]).dropna()
    rs_sma50 = sma(rs, 50)
    rs_up = bool(rs.iloc[-1] > rs_sma50.iloc[-1] and rs.iloc[-1] > rs.iloc[-20]) if len(rs) >= 70 else False

    close_at_60d_high = bool(latest["Close"] >= latest["high60"])
    ret20_positive = bool(latest["ret20"] > 0)

    metrics = {
        "price": float(latest["Close"]),
        "sma50": float(latest["sma50"]),
        "sma200": float(latest["sma200"]),
        "golden_cross_recent": golden_cross_recent,
        "price_above_200": price_above_200,
        "sma200_up": sma200_up,
        "rsi14": rsi_val,
        "rsi_regime": rsi_regime,
        "macd": float(latest["macd"]),
        "macd_signal": float(latest["macd_signal"]),
        "macd_hist": float(latest["macd_hist"]),
        "macd_bullish": macd_bullish,
        "atr_pct": float(latest["atr_pct"]),
        "atr_contraction_breakout": atr_contraction_breakout,
        "rs_up": rs_up,
        "macro_ok": True if not macro_enabled else macro_ok,
        "close_at_60d_high": close_at_60d_high,
        "ret20_positive": ret20_positive,
    }

    score, reasons = compute_score(metrics, macro_enabled=macro_enabled)
    metrics["score"] = score
    metrics["reasons"] = reasons
    return metrics


def run_screener(
    tickers: list[str],
    start_date: str,
    cache_dir: Path,
    results_path: Path,
    skipped_path: Path,
    macro_enabled: bool = True,
):
    results = []
    skipped = []

    spy_df = load_or_download_ticker("SPY", start_date, cache_dir)
    if spy_df.empty:
        raise RuntimeError("Unable to load SPY data required for RS and macro checks")

    macro_ok, macro_details = _macro_status(start_date, cache_dir)

    for ticker in tickers:
        try:
            df = load_or_download_ticker(ticker, start_date, cache_dir)
            if df.empty:
                skipped.append({"ticker": ticker, "reason": "download returned empty dataframe"})
                continue

            metrics = _calc_metrics(df, spy_df, macro_ok=macro_ok, macro_enabled=macro_enabled)
            metrics["ticker"] = ticker
            metrics["macro_ok"] = metrics["macro_ok"] and (macro_ok if macro_enabled else True)
            if macro_enabled:
                metrics["reasons"] += (
                    f" | Macro components spy_ok={macro_details['spy_ok']}"
                    f", vix_ok={macro_details['vix_ok']}, tnx_ok={macro_details['tnx_ok']}"
                )
            results.append(metrics)
        except Exception as exc:
            skipped.append({"ticker": ticker, "reason": str(exc)})

    results_df = pd.DataFrame(results)
    if not results_df.empty:
        ordered_cols = [
            "ticker", "score", "price", "sma50", "sma200", "golden_cross_recent", "price_above_200",
            "sma200_up", "rsi14", "rsi_regime", "macd", "macd_signal", "macd_hist", "macd_bullish",
            "atr_pct", "atr_contraction_breakout", "rs_up", "macro_ok", "reasons",
        ]
        results_df = results_df[ordered_cols].sort_values("score", ascending=False)

    skipped_df = pd.DataFrame(skipped)

    results_path.parent.mkdir(parents=True, exist_ok=True)
    skipped_path.parent.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(results_path, index=False)
    skipped_df.to_csv(skipped_path, index=False)

    return results_df, skipped_df
