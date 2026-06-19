"""
Aging Inventory Agent — API

Endpoints
  GET  /health             liveness check
  POST /analyze            score + recommend for a list of vehicles (JSON)
  POST /analyze/csv        same, but upload a CSV file
  POST /track              milestone tracking (30/45/60/75/90) with new-alert detection
  POST /track/csv          milestone tracking from an uploaded CSV
  POST /alerts/send        run tracking and dispatch email/SMS alerts

Run:  uvicorn app.main:app --reload
"""

import csv
import io
from datetime import date

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import AnalyzeRequest, TrackRequest, HealthResponse
from app.scoring import Vehicle, score_inventory
from app.recommend import build_recommendation
from app.tracker import track_vehicle
from app.marketcheck import enrich_vehicle
from app.alerts import dispatch_alerts

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── helpers ─────────────────────────────────────────────────────────────────
def _to_vehicle(d: dict) -> Vehicle:
    return Vehicle(
        vin=d["vin"], year=int(d["year"]), make=d["make"], model=d["model"],
        cost=float(d["cost"]), list_price=float(d["list_price"]),
        date_in_stock=d["date_in_stock"] if isinstance(d["date_in_stock"], date)
        else date.fromisoformat(d["date_in_stock"]),
        photos_count=int(d.get("photos_count", 0) or 0),
        leads_30d=int(d.get("leads_30d", 0) or 0),
        views_30d=int(d.get("views_30d", 0) or 0),
        market_avg_price=float(d["market_avg_price"]) if d.get("market_avg_price") else None,
        market_days_supply=int(d["market_days_supply"]) if d.get("market_days_supply") else None,
    )


def _parse_csv(raw: bytes):
    text = raw.decode("utf-8-sig")
    return [_to_vehicle(row) for row in csv.DictReader(io.StringIO(text))]


def _analyze(vehicles, apr):
    for v in vehicles:
        enrich_vehicle(v)            # fill market data if a key is configured
    scored = score_inventory(vehicles, apr=apr)
    results = [build_recommendation(s).__dict__ for s in scored]
    return {
        "analyzed": len(results),
        "high_priority": sum(1 for r in results if r["priority"] == "HIGH"),
        "total_monthly_bleed": round(sum(r["monthly_floorplan_bleed"] for r in results), 2),
        "results": results,
    }


def _track(vehicles, days_since):
    today = date.today()
    tracked = []
    for v in vehicles:
        enrich_vehicle(v)
        days_on_lot = max((today - v.date_in_stock).days, 0)
        t = track_vehicle(
            vin=v.vin, label=f"{v.year} {v.make} {v.model}",
            days_on_lot=days_on_lot, list_price=v.list_price, cost=v.cost,
            market_price=v.market_avg_price, days_since_last_check=days_since,
        )
        tracked.append(t)
    tracked.sort(key=lambda x: x.days_on_lot, reverse=True)
    return tracked


def _serialize_tracked(t):
    return {
        "vin": t.vin, "label": t.label, "days_on_lot": t.days_on_lot,
        "list_price": t.list_price, "market_price": t.market_price,
        "monthly_bleed": t.monthly_bleed, "next_milestone": t.next_milestone,
        "days_to_next": t.days_to_next, "alert": t.alert,
        "milestones": [
            {"day": m.day, "crossed": m.crossed, "newly_crossed": m.newly_crossed,
             "severity": m.severity, "action": m.action}
            for m in t.milestones
        ],
    }


# ── endpoints ───────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version=settings.VERSION)


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    vehicles = [_to_vehicle(v.model_dump()) for v in req.vehicles]
    return _analyze(vehicles, req.floorplan_apr)


@app.post("/analyze/csv")
async def analyze_csv(file: UploadFile = File(...),
                      floorplan_apr: float = Form(0.085)):
    vehicles = _parse_csv(await file.read())
    return _analyze(vehicles, floorplan_apr)


@app.post("/track")
def track(req: TrackRequest):
    vehicles = [_to_vehicle(v.model_dump()) for v in req.vehicles]
    tracked = _track(vehicles, req.days_since_last_check)
    return {
        "tracked": len(tracked),
        "new_alerts": [t.alert for t in tracked if t.alert],
        "vehicles": [_serialize_tracked(t) for t in tracked],
    }


@app.post("/track/csv")
async def track_csv(file: UploadFile = File(...),
                    days_since_last_check: int = Form(1)):
    vehicles = _parse_csv(await file.read())
    tracked = _track(vehicles, days_since_last_check)
    return {
        "tracked": len(tracked),
        "new_alerts": [t.alert for t in tracked if t.alert],
        "vehicles": [_serialize_tracked(t) for t in tracked],
    }


@app.post("/alerts/send")
async def alerts_send(file: UploadFile = File(...),
                      email: str = Form(""), sms: str = Form(""),
                      days_since_last_check: int = Form(1)):
    vehicles = _parse_csv(await file.read())
    tracked = _track(vehicles, days_since_last_check)
    new_alerts = [t for t in tracked if t.alert]
    return dispatch_alerts(new_alerts, email=email, sms=sms)
