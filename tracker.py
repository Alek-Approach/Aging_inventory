"""
Aging Inventory — Milestone Tracker
Dealers upload a CSV of their lot. Each vehicle is tracked against
five milestones: 30, 45, 60, 75, 90 days. As a unit crosses each one,
the system escalates its recommendation and flags it for an alert.

Designed so the same CSV can be re-uploaded daily/weekly — the tracker
compares each car's current age to the milestones and reports which
ones it has newly crossed since a given 'last_checked' date.
"""

import csv
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List

MILESTONES = [30, 45, 60, 75, 90]
APR = 0.085


@dataclass
class Milestone:
    day: int
    crossed: bool
    newly_crossed: bool          # crossed since last check → triggers alert
    severity: str                # WATCH / ACT / URGENT / CRITICAL
    action: str


@dataclass
class TrackedVehicle:
    vin: str
    label: str
    days_on_lot: int
    list_price: float
    market_price: Optional[float]
    monthly_bleed: float
    next_milestone: Optional[int]
    days_to_next: Optional[int]
    milestones: List[Milestone] = field(default_factory=list)
    alert: Optional[str] = None   # set if a milestone was newly crossed


def _severity(day: int) -> str:
    return {30: "WATCH", 45: "ACT", 60: "ACT", 75: "URGENT", 90: "CRITICAL"}[day]


def _action(day: int, list_price: float, market: Optional[float]) -> str:
    # Escalating play at each milestone.
    if day == 30:
        return ("First check-in: refresh photos & listing title, "
                "confirm price is within market.")
    if day == 45:
        if market and list_price > market * 1.02:
            return f"Reprice toward market (~{_usd(market)}). Add to email feature."
        return "Small test price cut (~2%). Boost on Marketplace + Vehicle Ads."
    if day == 60:
        return "Reprice at/just below market. Manager's Special + price-drop badge."
    if day == 75:
        return "Aggressive cut below market. Consider wholesale/auction backup plan."
    if day == 90:
        return ("Critical: price to move now or send to auction — "
                "floor-plan cost is eating the margin.")
    return ""


def _usd(n):
    return "$" + format(int(round(n)), ",")


def track_vehicle(vin, label, days_on_lot, list_price, cost,
                  market_price=None, days_since_last_check=1) -> TrackedVehicle:
    daily_fp = cost * APR / 365
    age_at_last_check = days_on_lot - days_since_last_check

    milestones, newest_alert = [], None
    for m in MILESTONES:
        crossed = days_on_lot >= m
        newly = crossed and age_at_last_check < m
        ms = Milestone(
            day=m, crossed=crossed, newly_crossed=newly,
            severity=_severity(m),
            action=_action(m, list_price, market_price),
        )
        milestones.append(ms)
        if newly:
            newest_alert = (f"{label} just hit {m} days. {ms.action}")

    upcoming = [m for m in MILESTONES if m > days_on_lot]
    nxt = upcoming[0] if upcoming else None

    return TrackedVehicle(
        vin=vin, label=label, days_on_lot=days_on_lot,
        list_price=round(list_price),
        market_price=round(market_price) if market_price else None,
        monthly_bleed=round(daily_fp * 30),
        next_milestone=nxt,
        days_to_next=(nxt - days_on_lot) if nxt else None,
        milestones=milestones,
        alert=newest_alert,
    )


def load_and_track(csv_path, today=None, days_since_last_check=1):
    today = today or date.today()
    tracked = []
    with open(csv_path, newline="") as f:
        for r in csv.DictReader(f):
            days_on_lot = max((today - date.fromisoformat(r["date_in_stock"])).days, 0)
            tracked.append(track_vehicle(
                vin=r["vin"],
                label=f'{r["year"]} {r["make"]} {r["model"]}',
                days_on_lot=days_on_lot,
                list_price=float(r["list_price"]),
                cost=float(r["cost"]),
                market_price=float(r["market_avg_price"]) if r.get("market_avg_price") else None,
                days_since_last_check=days_since_last_check,
            ))
    tracked.sort(key=lambda t: t.days_on_lot, reverse=True)
    return tracked
