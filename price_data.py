"""Fetch basic price and fundamental data for a stock ticker using yfinance."""

import yfinance as yf


def get_price_summary(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    history = stock.history(period="5d")

    if history.empty:
        raise ValueError(f"No price data found for ticker '{ticker}'")

    last_close = history["Close"].iloc[-1]
    prev_close = history["Close"].iloc[-2] if len(history) > 1 else last_close
    change = last_close - prev_close
    change_pct = (change / prev_close) * 100 if prev_close else 0

    info = stock.info  # company details (name, market cap, P/E, etc.)

    return {
        "ticker": ticker.upper(),
        "name": info.get("shortName", ticker.upper()),
        "price": round(last_close, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        # Wall Street analysts' own published 12-month price targets - real
        # published estimates, not something this script calculates or predicts.
        "analyst_target_mean": info.get("targetMeanPrice"),
        "analyst_target_low": info.get("targetLowPrice"),
        "analyst_target_high": info.get("targetHighPrice"),
        "analyst_count": info.get("numberOfAnalystOpinions"),
        "analyst_recommendation": info.get("recommendationKey"),
    }


if __name__ == "__main__":
    # Quick manual test: run `python price_data.py` to see it work on its own.
    summary = get_price_summary("AAPL")
    for key, value in summary.items():
        print(f"{key}: {value}")
