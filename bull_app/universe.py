from pathlib import Path


NASDAQ100 = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA", "AVGO", "COST",
    "ADBE", "NFLX", "PEP", "AMD", "CSCO", "INTC", "CMCSA", "TMUS", "TXN", "QCOM",
    "AMGN", "HON", "INTU", "AMAT", "ISRG", "BKNG", "ADP", "VRTX", "SBUX", "MDLZ",
    "GILD", "ADI", "PDD", "MU", "PANW", "REGN", "LRCX", "KLAC", "CRWD", "MELI",
    "SNPS", "CDNS", "FTNT", "MAR", "CSX", "MRVL", "ABNB", "ORLY", "MCHP", "PYPL",
    "ASML", "ADSK", "ROP", "WDAY", "CHTR", "CPRT", "IDXX", "NXPI", "KDP", "AEP",
    "MNST", "ROST", "EA", "XEL", "CTAS", "AZN", "TEAM", "ODFL", "DXCM", "LCID",
    "ILMN", "PAYX", "WBD", "PCAR", "FAST", "BIIB", "VRSK", "DLTR", "EXC", "BKR",
    "GFS", "KHC", "CCEP", "ANSS", "DDOG", "ZS", "CEG", "FANG", "ON", "GEHC",
    "SIRI", "CSGP", "TTWO", "MDB", "LULU", "ARM", "SMCI", "RIVN", "SPLK", "ALGN",
]


def parse_tickers(text: str) -> list[str]:
    raw = text.replace("\n", ",").split(",")
    cleaned = [t.strip().upper() for t in raw if t.strip()]
    return list(dict.fromkeys(cleaned))


def load_tickers(universe: str, custom_text: str, base_dir: Path) -> list[str]:
    if universe == "nasdaq100":
        return NASDAQ100

    tickers = parse_tickers(custom_text)
    if tickers:
        return tickers

    tickers_file = base_dir / "tickers.txt"
    if tickers_file.exists():
        return parse_tickers(tickers_file.read_text())

    return []
