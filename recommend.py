"""
Recommendation engine — combines the risk score with market-anchored
pricing and a stage-appropriate marketing play. One call per vehicle
produces everything the dashboard and alerts need.
"""

from dataclasses import dataclass, asdict
from typing import Optional

from app.scoring import ScoredVehicle
from app.pricing import recommend_price, PriceRecommendation


@dataclass
class Recommendation:
    vin: str
    headline: str
    priority: str
    pricing: dict
    marketing_action: str
    monthly_floorplan_bleed: float


def _priority(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def _marketing(s: ScoredVehicle) -> str:
    v = s.vehicle
    if v.photos_count < 8:
        return "Shoot full photo set (20+) + 360 spin — merchandising gap is suppressing leads."
    if v.leads_30d == 0 and s.days_in_stock >= 14:
        return "Launch paid boost: Facebook/Marketplace + Google Vehicle Ads. Refresh listing title."
    if s.days_in_stock >= 60:
        return "Feature in weekly email blast + homepage Manager's Special. Add price-drop badge."
    return "Maintain standard syndication."


def build_recommendation(s: ScoredVehicle) -> Recommendation:
    v = s.vehicle
    price: PriceRecommendation = recommend_price(
        current_price=v.list_price,
        days_on_lot=s.days_in_stock,
        market_price=v.market_avg_price,
        leads_30d=v.leads_30d,
    )
    return Recommendation(
        vin=v.vin,
        headline=f"{v.year} {v.make} {v.model} — {s.bucket} days, risk {s.risk_score}/100",
        priority=_priority(s.risk_score),
        pricing=asdict(price),
        marketing_action=_marketing(s),
        monthly_floorplan_bleed=round(s.daily_floorplan_cost * 30, 2),
    )
