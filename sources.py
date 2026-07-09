"""Filters out low-quality news domains observed polluting the free RSS
feeds (content mills, forums, social platforms) so reports stay closer to
actual reporting. This is a denylist, not a whitelist: most financial RSS
headlines route through syndication partners (finance.yahoo.com etc.) rather
than the original wire service, so an allow-only list would drop nearly
everything. Anything not explicitly blocked passes through with its
publisher domain attached for transparency."""

from urllib.parse import urlparse

BLOCKED_DOMAINS = {
    "247wallst.com",
    "trefis.com",
    "stocktwits.com",
    "investorshub.advfn.com",
    "fool.com",
}


def domain_of(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def is_blocked(url: str) -> bool:
    domain = domain_of(url)
    return any(domain == d or domain.endswith("." + d) for d in BLOCKED_DOMAINS)


def filter_reliable(items: list[dict], link_key: str = "link") -> list[dict]:
    """Drops items from low-quality domains and attaches a 'source' field to the rest."""
    kept = []
    for item in items:
        if is_blocked(item[link_key]):
            continue
        item = {**item, "source": domain_of(item[link_key])}
        kept.append(item)
    return kept
