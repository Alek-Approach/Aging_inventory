# API Reference

Base URL (dev): `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs` (Swagger UI, auto-generated)

All responses are JSON.

---

## GET /health

Liveness check.

```json
{ "status": "ok", "version": "1.0.0" }
```

---

## POST /analyze

Score and generate recommendations for a list of vehicles.

**Request**
```json
{
  "floorplan_apr": 0.085,
  "vehicles": [
    {
      "vin": "5XYZU3LB0JG333333",
      "year": 2019, "make": "Hyundai", "model": "Santa Fe",
      "cost": 21000, "list_price": 26995,
      "date_in_stock": "2026-04-12",
      "photos_count": 18, "leads_30d": 0, "views_30d": 120,
      "market_avg_price": 24800, "market_days_supply": 41
    }
  ]
}
```

**Response**
```json
{
  "analyzed": 1,
  "high_priority": 1,
  "total_monthly_bleed": 146.7,
  "results": [
    {
      "vin": "5XYZU3LB0JG333333",
      "headline": "2019 Hyundai Santa Fe — 60-89 days, risk 81.1/100",
      "priority": "HIGH",
      "monthly_floorplan_bleed": 146.7,
      "marketing_action": "Launch paid boost: ...",
      "pricing": {
        "current_price": 26995,
        "market_price": 24800,
        "recommended_price": 24300,
        "delta_vs_current": -2695,
        "pct_vs_current": -10.0,
        "position_vs_market_pct": -2.0,
        "rationale": "68 days on lot — set 2% below market ...",
        "confidence": "HIGH"
      }
    }
  ]
}
```

---

## POST /analyze/csv

Same as `/analyze` but accepts a CSV file upload.

**Request** — `multipart/form-data`
- `file`: the CSV (required)
- `floorplan_apr`: float (optional, default 0.085)

```bash
curl -F "file=@sample_inventory.csv" http://localhost:8000/analyze/csv
```

---

## POST /track

Milestone tracking with new-alert detection.

**Request**
```json
{
  "days_since_last_check": 7,
  "vehicles": [ /* same VehicleIn shape as /analyze */ ]
}
```

**Response**
```json
{
  "tracked": 5,
  "new_alerts": ["2020 Ford Fusion just hit 45 days. Reprice toward market ..."],
  "vehicles": [
    {
      "vin": "...", "label": "2020 Ford Fusion",
      "days_on_lot": 47, "list_price": 21995, "market_price": 20900,
      "monthly_bleed": 126, "next_milestone": 60, "days_to_next": 13,
      "alert": "2020 Ford Fusion just hit 45 days. ...",
      "milestones": [
        {"day": 30, "crossed": true,  "newly_crossed": false, "severity": "WATCH", "action": "..."},
        {"day": 45, "crossed": true,  "newly_crossed": true,  "severity": "ACT",   "action": "..."},
        {"day": 60, "crossed": false, "newly_crossed": false, "severity": "ACT",   "action": "..."}
      ]
    }
  ]
}
```

`days_since_last_check` controls which milestones count as "new". On a daily
job use `1`; if a dealer re-uploads after a week use `7`.

---

## POST /track/csv

Same as `/track` but accepts a CSV upload.

**Request** — `multipart/form-data`
- `file`: the CSV (required)
- `days_since_last_check`: int (optional, default 1)

---

## POST /alerts/send

Run tracking on an uploaded CSV and dispatch alerts for newly-crossed
milestones via email and/or SMS.

**Request** — `multipart/form-data`
- `file`: the CSV (required)
- `email`: recipient email (optional)
- `sms`: recipient phone in E.164 (optional)
- `days_since_last_check`: int (optional, default 1)

**Response**
```json
{ "sent": true, "channels": { "email": true }, "digest": "Inventory milestone alerts: ..." }
```

If no alert credentials are configured, the digest is logged instead of sent
and `channels` reflects `false` — useful in dev.
