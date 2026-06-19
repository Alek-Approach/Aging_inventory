"""
MarketCheck adapter.

Fetches live US market comps for a vehicle and returns
(market_avg_price, market_days_supply). Falls back to (None, None)
if no API key is configured or the call fails — the scoring engine
handles missing market data gracefully.

NOTE: the HTTP call shape below follows MarketCheck's documented
/search endpoint. Validate field names against your plan's API docs
before going live. Without a key, get_market_data() returns (None, None)
and the rest of the system keeps working on age + demand signals.
"""

import time
from typing import Optional, Tuple

import httpx

from app.config import settings

# Simple in-memory cache: { vin_or_ymmt: (timestamp, (price, supply)) }
_cache: dict = {}


def _cache_key(year, make, model, zip_code) -> str:
    return f"{year}|{make}|{model}|{zip_code}".lower()


def _cached(key):
    hit = _cache.get(key)
    if not hit:
        return None
    ts, value = hit
    if time.time() - ts > settings.MARKET_CACHE_TTL_HOURS * 3600:
        return None
    return value


def get_market_data(year: int, make: str, model: str,
                    zip_code: str = "", radius: int = 100
                    ) -> Tuple[Optional[float], Optional[int]]:
    """Return (market_avg_price, market_days_supply) or (None, None)."""
    if not settings.MARKETCHECK_API_KEY:
        return (None, None)

    key = _cache_key(year, make, model, zip_code)
    cached = _cached(key)
    if cached is not None:
        return cached

    params = {
        "api_key": settings.MARKETCHECK_API_KEY,
        "year": year,
        "make": make,
        "model": model,
        "radius": radius,
        "car_type": "used",
        "stats": "price,dom",   # request price + days-on-market stats
    }
    if zip_code:
        params["zip"] = zip_code

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{settings.MARKETCHECK_BASE_URL}/search/car/active",
                              params=params)
            resp.raise_for_status()
            data = resp.json()

        stats = data.get("stats", {})
        avg_price = stats.get("price", {}).get("mean")
        # days-supply proxy from mean days-on-market if explicit supply absent
        days_supply = stats.get("dom", {}).get("mean")

        result = (
            round(float(avg_price)) if avg_price else None,
            int(round(float(days_supply))) if days_supply else None,
        )
        _cache[key] = (time.time(), result)
        return result
    except Exception:
        # Never let a market-data failure break the pipeline.
        return (None, None)


def enrich_vehicle(v, zip_code: str = ""):
    """Fill market fields on a Vehicle in place if they're missing."""
    if v.market_avg_price is None:
        price, supply = get_market_data(v.year, v.make, v.model, zip_code)
        if price is not None:
            v.market_avg_price = price
        if supply is not None and v.market_days_supply is None:
            v.market_days_supply = supply
    return v
