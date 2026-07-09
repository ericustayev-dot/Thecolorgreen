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
