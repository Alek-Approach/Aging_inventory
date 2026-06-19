"""
Market-Anchored Pricing
Blends three inputs into one recommended price:
  1. current list price (where the dealer is now)
  2. market price (from MarketCheck comps)
  3. time on lot (age pressure pushes the target below market as it ages)

Returns all three reference points so the dealer sees the reasoning,
not just a number.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PriceRecommendation:
    current_price: float
    market_price: Optional[float]
    recommended_price: float
    delta_vs_current: float          # recommended - current (negative = cut)
    pct_vs_current: float
    position_vs_market_pct: Optional[float]   # where recommendation sits vs market
    rationale: str
    confidence: str                  # HIGH if market data present, else LOW


# How far relative to market we aim, by age. <1.0 = below market.
# The older it sits, the more we discount past market to force the turn.
def _market_factor(days: int) -> float:
    if days >= 90:
        return 0.97       # 3% under market — move it now
    if days >= 60:
        return 0.99       # just under market
    if days >= 45:
        return 1.00       # at market
    if days >= 30:
        return 1.01       # a hair above market
    return 1.03           # fresh: hold a premium


# Fallback ladder when there is NO market data: cut from current price by age.
def _no_market_cut(days: int) -> float:
    if days >= 90:
        return 0.94
    if days >= 60:
        return 0.97
    if days >= 45:
        return 0.985
    if days >= 30:
        return 0.995
    return 1.00


def recommend_price(current_price: float, days_on_lot: int,
                    market_price: Optional[float] = None,
                    leads_30d: int = 0) -> PriceRecommendation:

    if market_price:
        target = market_price * _market_factor(days_on_lot)

        # Soft demand for the car's age → nudge a little harder.
        if days_on_lot >= 21 and leads_30d == 0:
            target *= 0.99

        # Never recommend raising the price on an aging unit.
        if days_on_lot >= 45:
            target = min(target, current_price)

        recommended = round(target / 50) * 50   # round to nearest $50
        pos = (recommended - market_price) / market_price * 100
        confidence = "HIGH"

        if pos < -1.5:
            rationale = (f"{days_on_lot} days on lot — price {abs(pos):.0f}% "
                         f"below market to drive a fast sale.")
        elif abs(pos) <= 1.5:
            rationale = (f"{days_on_lot} days on lot — align to market to "
                         f"restart demand.")
        else:
            rationale = (f"Only {days_on_lot} days — hold a slight premium "
                         f"over market.")
    else:
        recommended = round(current_price * _no_market_cut(days_on_lot) / 50) * 50
        pos = None
        confidence = "LOW"
        rationale = (f"No market comp available — age-based "
                     f"{(1 - recommended / current_price) * 100:.0f}% adjustment "
                     f"from current price.")

    delta = recommended - current_price
    return PriceRecommendation(
        current_price=round(current_price),
        market_price=round(market_price) if market_price else None,
        recommended_price=recommended,
        delta_vs_current=round(delta),
        pct_vs_current=round(delta / current_price * 100, 1),
        position_vs_market_pct=round(pos, 1) if pos is not None else None,
        rationale=rationale,
        confidence=confidence,
    )
