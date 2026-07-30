"""Deep research report: pulls broader fundamentals (margins, growth, cash
flow, valuation) beyond what the quick stock card shows, and checks each one
against a fixed threshold - the same yardstick applied to every ticker.
No AI, no predictions - every number here is straight from the company's own
reported financials via Yahoo Finance."""

import yfinance as yf

from movers import classify_cap
from buy_score import compute_entry_price

SIGNAL_DESCRIPTIONS = {
    "Revenue growth (YoY)": "How much more the company sold this year vs. the same period last year - the clearest sign of whether the underlying business is actually growing.",
    "Operating margin": "The share of each revenue dollar left after running the core business, before interest and taxes - higher means the business itself is efficient.",
    "Net margin": "The share of each revenue dollar left as actual profit after everything, including interest and taxes.",
    "Free cash flow (latest quarter)": "Cash left over after paying for the equipment and investments needed to run the business. Positive means the company funds itself; negative means it's burning cash or investing heavily for future growth.",
    "P/E (trailing)": "How many dollars investors are currently paying for every $1 of the company's past year of profit. Higher means more future growth is already priced in - and more room to disappoint.",
    "Return on equity": "How efficiently the company turns shareholders' invested money into profit.",
}


def fmt_pct(x) -> str:
    return f"{x * 100:.1f}%" if x is not None else "N/A"


def fmt_usd_big(x) -> str:
    if x is None:
        return "N/A"
    for unit, div in [("T", 1e12), ("B", 1e9), ("M", 1e6)]:
        if abs(x) >= div:
            return f"${x / div:.2f}{unit}"
    return f"${x:,.0f}"


def _signal(value, good_threshold, bad_threshold, higher_is_better=True) -> str:
    """'good' / 'caution' / 'bad' against a fixed threshold - not tuned per
    stock, so the same bar applies whether it's Tesla or a utility company."""
    if value is None:
        return "unknown"
    if higher_is_better:
        if value >= good_threshold:
            return "good"
        if value <= bad_threshold:
            return "bad"
        return "caution"
    if value <= good_threshold:
        return "good"
    if value >= bad_threshold:
        return "bad"
    return "caution"


def _latest_quarterly_cash_flow(stock: yf.Ticker) -> dict:
    try:
        cf = stock.quarterly_cashflow
        if cf is None or cf.empty:
            return {}
        latest_col = cf.columns[0]
        prior_col = cf.columns[1] if cf.shape[1] > 1 else None

        def get(row_name, col):
            if col is None or row_name not in cf.index:
                return None
            val = cf.loc[row_name, col]
            if val is None or val != val:  # NaN check without pandas import
                return None
            return float(val)

        def fcf_for(col):
            fcf = get("Free Cash Flow", col)
            if fcf is not None:
                return fcf
            ocf = get("Operating Cash Flow", col) or get("Total Cash From Operating Activities", col)
            capex = get("Capital Expenditure", col)
            return ocf + capex if ocf is not None and capex is not None else None

        return {
            "quarter_end": str(latest_col.date()) if hasattr(latest_col, "date") else str(latest_col),
            "operating_cash_flow": get("Operating Cash Flow", latest_col) or get("Total Cash From Operating Activities", latest_col),
            "capital_expenditure": get("Capital Expenditure", latest_col),
            "free_cash_flow": fcf_for(latest_col),
            "free_cash_flow_prior_quarter": fcf_for(prior_col),
        }
    except Exception:
        return {}


def compute_deep_research(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info
    cash = _latest_quarterly_cash_flow(stock)

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    fifty_two_high = info.get("fiftyTwoWeekHigh")
    fifty_two_low = info.get("fiftyTwoWeekLow")
    pct_from_high = ((price - fifty_two_high) / fifty_two_high * 100) if price and fifty_two_high else None

    cap = classify_cap(info.get("marketCap"))
    entry_price = compute_entry_price(price, info.get("targetMeanPrice"), info.get("beta"), cap)

    fundamentals = {
        "revenue_ttm": info.get("totalRevenue"),
        "revenue_growth_yoy": info.get("revenueGrowth"),
        "earnings_growth_yoy": info.get("earningsGrowth"),
        "operating_margin": info.get("operatingMargins"),
        "net_margin": info.get("profitMargins"),
        "gross_margin": info.get("grossMargins"),
        "return_on_equity": info.get("returnOnEquity"),
    }

    valuation = {
        "pe_trailing": info.get("trailingPE"),
        "pe_forward": info.get("forwardPE"),
        "ps_ratio": info.get("priceToSalesTrailing12Months"),
        "ev_to_ebitda": info.get("enterpriseToEbitda"),
        "fifty_two_week_high": fifty_two_high,
        "fifty_two_week_low": fifty_two_low,
        "pct_from_52w_high": pct_from_high,
    }

    signals = []
    if fundamentals["revenue_growth_yoy"] is not None:
        signals.append({
            "label": "Revenue growth (YoY)",
            "value": fmt_pct(fundamentals["revenue_growth_yoy"]),
            "signal": _signal(fundamentals["revenue_growth_yoy"], 0.15, 0.0),
        })
    if fundamentals["operating_margin"] is not None:
        signals.append({
            "label": "Operating margin",
            "value": fmt_pct(fundamentals["operating_margin"]),
            "signal": _signal(fundamentals["operating_margin"], 0.15, 0.05),
        })
    if fundamentals["net_margin"] is not None:
        signals.append({
            "label": "Net margin",
            "value": fmt_pct(fundamentals["net_margin"]),
            "signal": _signal(fundamentals["net_margin"], 0.10, 0.0),
        })
    if cash.get("free_cash_flow") is not None:
        signals.append({
            "label": "Free cash flow (latest quarter)",
            "value": fmt_usd_big(cash["free_cash_flow"]),
            "signal": "good" if cash["free_cash_flow"] > 0 else "bad",
        })
    if valuation["pe_trailing"] is not None:
        signals.append({
            "label": "P/E (trailing)",
            "value": f"{valuation['pe_trailing']:.1f}x",
            "signal": _signal(valuation["pe_trailing"], 25, 60, higher_is_better=False),
        })
    if fundamentals["return_on_equity"] is not None:
        signals.append({
            "label": "Return on equity",
            "value": fmt_pct(fundamentals["return_on_equity"]),
            "signal": _signal(fundamentals["return_on_equity"], 0.15, 0.0),
        })

    for s in signals:
        s["description"] = SIGNAL_DESCRIPTIONS.get(s["label"], "")

    return {
        "ticker": ticker.upper(),
        "fundamentals": fundamentals,
        "valuation": valuation,
        "cash_flow": cash,
        "signals": signals,
        "entry_price": entry_price,
        "current_price": price,
    }


if __name__ == "__main__":
    # Quick manual test: run `python deep_research.py` to see it work on its own.
    result = compute_deep_research("AAPL")
    for s in result["signals"]:
        print(f"{s['label']}: {s['value']} ({s['signal']})")
