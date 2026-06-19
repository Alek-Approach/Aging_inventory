"""
Aging Inventory — Scoring Engine
Scores each vehicle on days-in-stock, price-to-market, lead velocity,
and accruing floor-plan cost to produce a single, rankable risk score.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ---- Tunable business assumptions (override per dealer) ---------------------
DEFAULT_FLOORPLAN_APR = 0.085        # annual interest on floor-plan financing
TARGET_TURN_DAYS = 45               # dealer's goal: sell within N days
AGE_BUCKETS = [30, 60, 90]          # alert thresholds


@dataclass
class Vehicle:
    vin: str
    year: int
    make: str
    model: str
    cost: float                      # what the dealer paid / floor-planned amount
    list_price: float
    date_in_stock: date
    photos_count: int = 0
    leads_30d: int = 0               # leads in last 30 days
    views_30d: int = 0
    market_avg_price: Optional[float] = None   # comp price from market data
    market_days_supply: Optional[int] = None   # lower = hotter segment


@dataclass
class ScoredVehicle:
    vehicle: Vehicle
    days_in_stock: int
    bucket: str
    risk_score: float                # 0-100, higher = act sooner
    floorplan_cost_to_date: float
    daily_floorplan_cost: float
    price_to_market_pct: Optional[float]
    drivers: list = field(default_factory=list)   # human-readable reasons


def _bucket(days: int) -> str:
    if days >= 90:
        return "90+"
    if days >= 60:
        return "60-89"
    if days >= 30:
        return "30-59"
    return "0-29"


def score_vehicle(v: Vehicle, today: Optional[date] = None,
                  apr: float = DEFAULT_FLOORPLAN_APR) -> ScoredVehicle:
    today = today or date.today()
    days = max((today - v.date_in_stock).days, 0)

    daily_fp = v.cost * apr / 365.0
    fp_to_date = daily_fp * days

    drivers = []
    score = 0.0

    # 1. Age pressure (0-40 pts). Ramps up past the target turn window.
    age_ratio = days / TARGET_TURN_DAYS
    age_pts = min(age_ratio * 25, 40)
    score += age_pts
    if days >= 90:
        drivers.append(f"Critical: {days} days in stock (90+)")
    elif days >= 60:
        drivers.append(f"Aging: {days} days in stock (60+)")
    elif days >= 30:
        drivers.append(f"Watch: {days} days in stock (30+)")

    # 2. Price vs market (0-25 pts). Priced above market = harder to move.
    p2m = None
    if v.market_avg_price:
        p2m = (v.list_price - v.market_avg_price) / v.market_avg_price * 100
        if p2m > 0:
            price_pts = min(p2m * 1.5, 25)
            score += price_pts
            if p2m >= 3:
                drivers.append(f"Priced {p2m:.1f}% above market")

    # 3. Demand signal (0-20 pts). Low lead velocity for its age = stale.
    if days >= 14:
        if v.leads_30d == 0:
            score += 20
            drivers.append("No leads in 30 days")
        elif v.leads_30d <= 2:
            score += 10
            drivers.append(f"Weak demand ({v.leads_30d} leads/30d)")

    # 4. Hot-segment penalty (0-10 pts). Sitting in a fast-moving segment is worse.
    if v.market_days_supply is not None and v.market_days_supply < 45 and days >= 30:
        score += 10
        drivers.append(f"Slow despite hot segment ({v.market_days_supply}d supply)")

    # 5. Merchandising gap (0-5 pts). Too few photos suppresses leads.
    if v.photos_count < 8:
        score += 5
        drivers.append(f"Only {v.photos_count} photos (recommend 20+)")

    return ScoredVehicle(
        vehicle=v,
        days_in_stock=days,
        bucket=_bucket(days),
        risk_score=round(min(score, 100), 1),
        floorplan_cost_to_date=round(fp_to_date, 2),
        daily_floorplan_cost=round(daily_fp, 2),
        price_to_market_pct=round(p2m, 1) if p2m is not None else None,
        drivers=drivers,
    )


def score_inventory(vehicles, today=None, apr=DEFAULT_FLOORPLAN_APR):
    scored = [score_vehicle(v, today, apr) for v in vehicles]
    scored.sort(key=lambda s: s.risk_score, reverse=True)
    return scored
