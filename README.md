# Aging Inventory Agent

An AI agent for car dealers that flags vehicles sitting too long, scores each
unit by **cost of inaction** (accruing floor-plan interest), and recommends a
**market-anchored price** and a stage-appropriate marketing play. Dealers
upload a CSV (or connect a feed) and get alerts at **30 · 45 · 60 · 75 · 90
days**.

```
┌────────────┐   CSV / JSON / DMS feed   ┌─────────────────────────┐
│  Dealer    │ ────────────────────────▶ │  FastAPI backend        │
│  inventory │                           │  • scoring engine       │
└────────────┘                           │  • market-anchored price│
       ▲                                 │  • milestone tracker    │
       │  alerts (email / SMS)           │  • MarketCheck adapter  │
       │                                 │  • alert dispatch       │
┌────────────┐    REST /api              └─────────────────────────┘
│  React app │ ◀───────────────────────────────────┘
└────────────┘
```

## Repository layout

```
backend/          FastAPI service (Python 3.12)
  app/
    scoring.py        risk scoring (age, price-vs-market, demand, bleed)
    pricing.py        market-anchored price recommendation + age fallback
    tracker.py        30/45/60/75/90-day milestone tracking + new-alert logic
    recommend.py      combines score + price + marketing into one rec
    marketcheck.py    optional live market-data adapter (cached)
    alerts.py         email (SendGrid) + SMS (Twilio) dispatch
    scheduler.py      daily cron runner for automated alerts
    main.py           API endpoints
  tests/              pytest suite (10 tests)
frontend/         React + Vite app
  src/
    components/       UploadTracker, AnalysisView, MilestoneTrack
    lib/              api client + theme tokens
docs/             architecture + API reference
docker-compose.yml   one-command full stack
```

## Quick start (Docker — recommended)

```bash
cp backend/.env.example backend/.env     # fill in keys (optional to start)
docker compose up --build
```

- Frontend → http://localhost:8080
- API docs → http://localhost:8000/docs

## Quick start (local dev)

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload          # http://localhost:8000
pytest                                 # run tests
```

**Frontend**
```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173
```

The dev server proxies `/api` → `http://localhost:8000`, so run both together.

## How it works

**Scoring (0–100).** Age pressure, price-vs-market, demand (leads), hot-segment
penalty, and merchandising gap. ≥70 HIGH, 40–69 MEDIUM, <40 LOW.

**Pricing.** Anchors to the MarketCheck price, then shifts by time on lot:
fresh units hold a slight premium, 45-day units sit at market, 90+ day units
go below market to force the turn. With no market data it falls back to an
age-based cut and labels the rec `AGE-BASED` instead of `MARKET-BACKED`.

**Milestones.** Every unit is tracked against 30/45/60/75/90 days. The tracker
compares each car's age to its age at the last check and only fires alerts for
milestones **newly crossed**, so dealers aren't spammed on re-upload.

## Going live

- **Market data:** add `MARKETCHECK_API_KEY` to `backend/.env`. Without it the
  system runs on age + demand signals.
- **Alerts:** add SendGrid and/or Twilio credentials, then schedule the runner
  (`python -m app.scheduler`) via cron or the commented `scheduler` service in
  `docker-compose.yml`.
- **DMS feeds:** replace `scheduler.load_dealer_feeds()` with your storage/DB
  lookup of each dealer's latest pull. Normalize any feed (CDK, Reynolds,
  vAuto) into the CSV columns below.

## CSV format

```
vin,year,make,model,cost,list_price,date_in_stock,photos_count,leads_30d,views_30d,market_avg_price,market_days_supply
```

`cost` is the floor-planned amount. `date_in_stock` is ISO (YYYY-MM-DD).
The last five columns are optional. A sample is at `backend/sample_inventory.csv`.

See `docs/` for the architecture and API reference.

## License

MIT
