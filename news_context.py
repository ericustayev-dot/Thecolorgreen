"""Tags a headline with a rough category and a short note on what that TYPE
of event has historically tended to mean for markets. This is general
historical pattern context, not a prediction of what will happen this time -
the same headline category can play out differently depending on scale,
timing, and what's already priced in."""

CATEGORY_RULES = [
    ("Geopolitical conflict", ["strike", "strikes", "war", "military", "missile", "invasion", "attack", "nuclear", "troops", "conflict"],
     "Armed conflict and military escalation have historically increased volatility and safe-haven demand (gold, US dollar), and pushed oil prices up when producing regions are involved."),
    ("Central bank / monetary policy", ["fed ", "federal reserve", "interest rate", "rate cut", "rate hike", "inflation", "central bank"],
     "Central bank decisions move bond yields directly, which has often had an inverse relationship with growth-stock valuations and gold."),
    ("Trade / sanctions", ["tariff", "trade deal", "export ban", "sanction", "trade war"],
     "Tariffs and sanctions have tended to hit specific sectors directly (manufacturing, tech supply chains, commodities) and can move currencies."),
    ("Elections / political instability", ["election", "campaign", "senate", "president", "government shutdown", "impeachment", "resign"],
     "Political uncertainty has typically raised short-term volatility broadly; sector-specific impact depends on which policies are actually at stake."),
    ("Natural disaster / industrial accident", ["earthquake", "flood", "hurricane", "wildfire", "explosion", "factory fire", "fire kills"],
     "Usually a localized disruption - has tended to affect specific supply chains, insurers, or regional producers, with limited broad market impact historically."),
]


def explain(title: str) -> dict:
    lower = title.lower()
    for category, keywords, explanation in CATEGORY_RULES:
        if any(kw in lower for kw in keywords):
            return {"category": category, "explanation": explanation}
    return {"category": "Other", "explanation": "No strong historical market pattern is typically tied to this type of headline."}


# Same idea, but for headlines about a single company rather than world/macro
# events - a rule-based summary of what a headline is about and what that
# TYPE of news has tended to mean, not a prediction for this specific case.
STOCK_CATEGORY_RULES = [
    ("Earnings", ["beats", "misses", "quarterly results", "earnings report", "q1 ", "q2 ", "q3 ", "q4 ", "eps", "revenue"],
     "Earnings news reflects actual reported financial performance. Beats have tended to lift a stock short-term and misses to pressure it, though the market's reaction also depends heavily on forward guidance."),
    ("Analyst rating", ["upgrade", "downgrade", "price target", "initiates coverage", "raised to", "cut to", "buy rating", "sell rating", "outperform", "underperform", "overweight"],
     "Analyst rating changes reflect one firm's updated opinion, not new company fundamentals by themselves - they've tended to move a stock briefly, with the effect fading if not backed by real business change."),
    ("Merger / acquisition", ["acquisition", "acquire", "merger", "buyout", "takeover", "to be acquired", "deal to buy"],
     "M&A news has tended to move the target company's stock toward the offer price and the acquirer's stock based on how the market judges the deal's cost and strategic fit."),
    ("Guidance / outlook", ["guidance", "forecast", "outlook cut", "outlook raised", "lowers outlook", "raises outlook"],
     "Guidance changes signal management's own view of future performance - cuts have tended to weigh on a stock even more than a single quarter's miss, since they reset future expectations."),
    ("Leadership change", ["ceo", "resigns", "steps down", "names new", "appoints", "executive departure"],
     "Leadership changes add uncertainty about strategic direction - the market's reaction has tended to depend on whether the change looks planned or abrupt."),
    ("Legal / regulatory", ["lawsuit", "investigation", "sec probe", "antitrust", "settlement", "fine", "regulatory", "subpoena"],
     "Legal and regulatory issues create open-ended financial and reputational risk - the market impact has tended to scale with the size of the potential penalty or business disruption."),
    ("Buyback / dividend", ["buyback", "share repurchase", "dividend", "stock split"],
     "Buybacks and dividends return cash to shareholders and can signal management confidence, though they don't reflect new operating performance by themselves."),
    ("Insider / institutional activity", ["insider buying", "insider selling", "institutional stake", "13f", "hedge fund bought", "hedge fund sold"],
     "Insider and institutional trades are sometimes read as a confidence signal, but funds trade for many reasons (rebalancing, redemptions) unrelated to their view of the company."),
    ("Price move", ["shares jump", "shares fall", "shares soar", "shares plunge", "stock rises", "stock drops", "stock rallies", "stock tumbles", "surges", "sinks"],
     "This headline is describing a price move itself rather than a new underlying event - worth checking what's actually driving it before reading too much into the move alone."),
]


def explain_stock_headline(title: str) -> dict:
    lower = title.lower()
    for category, keywords, explanation in STOCK_CATEGORY_RULES:
        if any(kw in lower for kw in keywords):
            return {"category": category, "explanation": explanation}
    return {"category": "Company news", "explanation": "General company-specific news that doesn't fit a common pattern - worth reading the full article for context."}
