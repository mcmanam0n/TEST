from __future__ import annotations


def compute_score(metrics: dict, macro_enabled: bool = True) -> tuple[int, str]:
    checks = {
        "golden_cross_recent": (20, bool(metrics.get("golden_cross_recent"))),
        "macd_bullish": (15, bool(metrics.get("macd_bullish"))),
        "rs_up": (15, bool(metrics.get("rs_up"))),
        "atr_contraction_breakout": (10, bool(metrics.get("atr_contraction_breakout"))),
        "macro_ok": (20, True if not macro_enabled else bool(metrics.get("macro_ok"))),
        "close_at_60d_high": (10, bool(metrics.get("close_at_60d_high"))),
        "ret20_positive": (10, bool(metrics.get("ret20_positive"))),
    }

    score = sum(weight for weight, passed in checks.values() if passed)

    hard_gate = (
        bool(metrics.get("price_above_200"))
        and bool(metrics.get("sma200_up"))
        and bool(metrics.get("rsi_regime"))
    )

    if not hard_gate:
        score = min(score, 49)

    failed = [name for name, (_, passed) in checks.items() if not passed]
    passed = [name for name, (_, passed) in checks.items() if passed]

    reasons_parts = []
    if failed:
        reasons_parts.append("Failed: " + ", ".join(failed))
    if passed:
        reasons_parts.append("Passed: " + ", ".join(passed))
    if not hard_gate:
        reasons_parts.append("Hard gate cap applied")

    return int(score), " | ".join(reasons_parts)
