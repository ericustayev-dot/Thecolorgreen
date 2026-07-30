"""Computes a quantitative buy/no-buy weight scale for a stock: analyst-target
upside weighed against estimated risk. This is a transparent formula, not
AI-generated - plain reward-vs-risk math using data already fetched for the
price card (analyst target, beta), so it costs nothing extra to compute.

The logic: a large upside pulls the scale heavily toward "buy" even with
above-average risk. A small upside gets dragged toward "no buy" once risk is
factored in, even though the raw upside number is technically positive.
This is a heuristic, not investment advice - it doesn't know about anything
that isn't already reflected in the analyst target price or the stock's
historical volatility (beta)."""

MARKET_BASELINE_VOLATILITY = 18.0  # rough long-run S&P 500 annualized volatility, %

# Used only when a stock has no beta on file (common for very small/new
# listings) - smaller companies tend to be more volatile on average.
CAP_DEFAULT_BETA = {
    "mega": 1.0,
    "large": 1.1,
    "mid": 1.4,
    "small": 1.8,
}

RISK_WEIGHT = 0.5
SCALE = 2.0


def estimate_volatility_pct(beta, cap: str) -> float:
    effective_beta = beta if beta else CAP_DEFAULT_BETA.get(cap, 1.5)
    return effective_beta * MARKET_BASELINE_VOLATILITY


def compute_buy_weight(price: float, target_mean, beta, cap: str) -> dict:
    if not target_mean or not price:
        return None

    upside_pct = (target_mean - price) / price * 100
    volatility_pct = estimate_volatility_pct(beta, cap)
    score = upside_pct - RISK_WEIGHT * volatility_pct
    buy_pct = max(5, min(95, round(50 + score * SCALE)))

    return {
        "upside_pct": round(upside_pct, 1),
        "volatility_pct": round(volatility_pct, 1),
        "used_default_beta": beta is None,
        "buy_pct": buy_pct,
        "no_buy_pct": 100 - buy_pct,
    }
