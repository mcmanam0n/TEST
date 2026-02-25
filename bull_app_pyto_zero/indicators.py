from statistics import median


def sma(values, period):
    out = [None] * len(values)
    if period <= 0:
        return out
    window_sum = 0.0
    for i, v in enumerate(values):
        window_sum += v
        if i >= period:
            window_sum -= values[i - period]
        if i >= period - 1:
            out[i] = window_sum / period
    return out


def ema(values, period):
    out = [None] * len(values)
    if not values or period <= 0:
        return out
    k = 2.0 / (period + 1)
    ema_val = values[0]
    out[0] = ema_val
    for i in range(1, len(values)):
        ema_val = values[i] * k + ema_val * (1 - k)
        out[i] = ema_val
    return out


def rsi_wilder(closes, period=14):
    n = len(closes)
    out = [None] * n
    if n <= period:
        return out
    gains = []
    losses = []
    for i in range(1, period + 1):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    out[period] = 100.0 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))

    for i in range(period + 1, n):
        diff = closes[i] - closes[i - 1]
        gain = max(diff, 0.0)
        loss = max(-diff, 0.0)
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        out[i] = 100.0 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))
    return out


def macd(closes):
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd_line = [None if (a is None or b is None) else a - b for a, b in zip(ema12, ema26)]
    macd_values = [0.0 if v is None else v for v in macd_line]
    signal = ema(macd_values, 9)
    hist = [None if m is None else m - signal[i] for i, m in enumerate(macd_line)]
    return macd_line, signal, hist


def atr(highs, lows, closes, period=14):
    n = len(closes)
    tr = [None] * n
    for i in range(n):
        if i == 0:
            tr[i] = highs[i] - lows[i]
        else:
            tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
    out = [None] * n
    if n <= period:
        return out
    first = sum(t for t in tr[1:period + 1] if t is not None) / period
    out[period] = first
    prev = first
    for i in range(period + 1, n):
        prev = ((prev * (period - 1)) + tr[i]) / period
        out[i] = prev
    return out


def golden_cross_recent(sma50, sma200, lookback=60):
    start = max(1, len(sma50) - lookback)
    for i in range(start, len(sma50)):
        y50, y200 = sma50[i - 1], sma200[i - 1]
        t50, t200 = sma50[i], sma200[i]
        if None in (y50, y200, t50, t200):
            continue
        if y50 <= y200 and t50 > t200:
            return True
    return False


def atr_contraction_breakout(atr_pct, closes, highs):
    if len(closes) < 61:
        return False
    valid_atr = [x for x in atr_pct[-60:] if x is not None]
    if not valid_atr:
        return False
    prior_high = max(highs[-21:-1])
    return atr_pct[-1] is not None and atr_pct[-1] < median(valid_atr) and closes[-1] > prior_high


def rs_up(rs_series):
    if len(rs_series) < 60:
        return False
    rs_sma50 = sma(rs_series, 50)
    last = rs_series[-1]
    base_idx = max(0, len(rs_series) - 21)
    rising = rs_series[-1] > rs_series[base_idx]
    return rs_sma50[-1] is not None and last > rs_sma50[-1] and rising
