def filter_tickers(tickers: list) -> list:
    return [ticker for ticker in tickers if ticker.isupper() and "^" not in ticker and "/" not in ticker]