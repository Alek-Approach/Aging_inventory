"""Backend test suite. Run with: pytest"""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.scoring import Vehicle, score_vehicle
from app.pricing import recommend_price
from app.tracker import track_vehicle

client = TestClient(app)
TODAY = date(2026, 6, 19)


# ── scoring ──────────────────────────────────────────────────────────────────
def test_fresh_vehicle_low_risk():
    v = Vehicle("V1", 2022, "Ford", "F-150", 39000, 44995,
                TODAY - timedelta(days=10), photos_count=24, leads_30d=12,
                market_avg_price=45200, market_days_supply=22)
    s = score_vehicle(v, today=TODAY)
    assert s.risk_score < 40
    assert s.bucket == "0-29"


def test_aging_no_leads_high_risk():
    v = Vehicle("V2", 2019, "Hyundai", "Santa Fe", 21000, 26995,
                TODAY - timedelta(days=68), photos_count=18, leads_30d=0,
                market_avg_price=24800, market_days_supply=41)
    s = score_vehicle(v, today=TODAY)
    assert s.risk_score >= 70
    assert "No leads in 30 days" in s.drivers


# ── pricing ──────────────────────────────────────────────────────────────────
def test_pricing_with_market_pushes_below_when_old():
    r = recommend_price(29995, 103, market_price=27200, leads_30d=0)
    assert r.confidence == "HIGH"
    assert r.recommended_price < 27200      # below market to force the turn


def test_pricing_without_market_falls_back():
    r = recommend_price(21995, 62, market_price=None)
    assert r.confidence == "LOW"
    assert r.recommended_price < 21995      # age-based cut


def test_pricing_never_raises_old_units():
    r = recommend_price(20000, 60, market_price=30000)  # priced well under market
    assert r.recommended_price <= 20000


# ── tracker ──────────────────────────────────────────────────────────────────
def test_milestone_newly_crossed():
    # 47 days now, was 40 a week ago → just crossed 45.
    t = track_vehicle("V3", "2020 Ford Fusion", 47, 21995, 18000,
                      market_price=20900, days_since_last_check=7)
    crossed_45 = [m for m in t.milestones if m.day == 45][0]
    assert crossed_45.newly_crossed is True
    assert t.alert is not None


def test_milestone_not_re_alerted():
    # 47 days, last checked yesterday → 45 was crossed earlier, not new.
    t = track_vehicle("V4", "2020 Ford Fusion", 47, 21995, 18000,
                      days_since_last_check=1)
    assert t.alert is None


# ── API ──────────────────────────────────────────────────────────────────────
def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_endpoint():
    payload = {"vehicles": [{
        "vin": "V5", "year": 2019, "make": "Hyundai", "model": "Santa Fe",
        "cost": 21000, "list_price": 26995, "date_in_stock": "2026-04-12",
        "photos_count": 18, "leads_30d": 0, "market_avg_price": 24800,
        "market_days_supply": 41,
    }]}
    r = client.post("/analyze", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["analyzed"] == 1
    assert body["results"][0]["priority"] == "HIGH"


def test_track_endpoint():
    payload = {"days_since_last_check": 7, "vehicles": [{
        "vin": "V6", "year": 2020, "make": "Ford", "model": "Fusion",
        "cost": 18000, "list_price": 21995, "date_in_stock": "2026-05-03",
        "market_avg_price": 20900,
    }]}
    r = client.post("/track", json=payload)
    assert r.status_code == 200
    assert r.json()["tracked"] == 1
