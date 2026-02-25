WEIGHTS = {
    "golden_cross_recent": 20,
    "macd_bullish": 15,
    "rs_up": 15,
    "atr_contraction_breakout": 10,
    "close_60d_high": 10,
    "ret20_positive": 10,
    "sma50_over_sma200": 10,
    "close_over_sma50": 10,
}


HARD_GATES = ["price_above_200", "sma200_up", "rsi_regime"]
STRICT_REQUIRED = HARD_GATES + ["macd_bullish", "rs_up"]


def score_row(flags):
    score = 0
    for key, weight in WEIGHTS.items():
        if flags.get(key):
            score += weight
    if any(not flags.get(g) for g in HARD_GATES):
        score = min(score, 49)
    return score


def build_reasons(flags):
    fails = [k for k, v in flags.items() if v is False and k in (HARD_GATES + ["macd_bullish", "rs_up", "golden_cross_recent", "atr_contraction_breakout"])]
    passes = [k for k, v in flags.items() if v is True and k in ("price_above_200", "sma200_up", "rsi_regime", "macd_bullish", "rs_up", "golden_cross_recent")]
    msg = []
    if fails:
        msg.append("failed:" + ",".join(fails[:4]))
    if passes:
        msg.append("passes:" + ",".join(passes[:2]))
    return "; ".join(msg) if msg else "mixed signals"


def strict_pass(flags):
    return all(flags.get(k) for k in STRICT_REQUIRED)
