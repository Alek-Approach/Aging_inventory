"""
Scheduled alert runner.

Run this once a day (cron, systemd timer, or a container scheduler).
It reads each dealer's latest inventory feed, runs milestone tracking,
and dispatches alerts for anything newly crossed in the last 24h.

In production, replace `load_dealer_feeds()` with a DB/storage lookup
of each dealer's most recent CSV or DMS pull. This file shows the loop.

Example cron (daily at 7am):
    0 7 * * *  cd /app && python -m app.scheduler
"""

import logging
from datetime import date

from app.scoring import Vehicle
from app.tracker import track_vehicle
from app.marketcheck import enrich_vehicle
from app.alerts import dispatch_alerts

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("scheduler")


def load_dealer_feeds():
    """
    Yield (dealer, vehicles) tuples.
    Stub: replace with real storage/DB lookup per dealer.
    """
    sample = {
        "name": "Demo Motors",
        "email": "sales@demomotors.example",
        "sms": "",
        "vehicles": [],   # populate from the dealer's latest upload
    }
    return [sample]


def run_once():
    today = date.today()
    for dealer in load_dealer_feeds():
        tracked = []
        for v in dealer["vehicles"]:
            vehicle = v if isinstance(v, Vehicle) else Vehicle(**v)
            enrich_vehicle(vehicle)
            days_on_lot = max((today - vehicle.date_in_stock).days, 0)
            tracked.append(track_vehicle(
                vin=vehicle.vin,
                label=f"{vehicle.year} {vehicle.make} {vehicle.model}",
                days_on_lot=days_on_lot, list_price=vehicle.list_price,
                cost=vehicle.cost, market_price=vehicle.market_avg_price,
                days_since_last_check=1,   # daily run
            ))

        new_alerts = [t for t in tracked if t.alert]
        if new_alerts:
            log.info("%s: %d new alert(s)", dealer["name"], len(new_alerts))
            dispatch_alerts(new_alerts, email=dealer.get("email", ""),
                            sms=dealer.get("sms", ""))
        else:
            log.info("%s: no new alerts", dealer["name"])


if __name__ == "__main__":
    run_once()
