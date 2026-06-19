# Architecture

## Overview

A two-service system: a stateless **FastAPI backend** that holds all the
business logic, and a **React frontend** that's a thin client over the API.
Everything is driven by a single normalized vehicle record, so any data
source (CSV upload, DMS feed, direct JSON) flows through the same pipeline.

## Data flow

1. **Ingest** — a dealer's inventory arrives as CSV upload, JSON, or a
   scheduled DMS pull. All paths normalize to the `Vehicle` dataclass.
2. **Enrich** — `marketcheck.enrich_vehicle()` fills `market_avg_price` and
   `market_days_supply` if a key is configured and the fields are blank.
   Results are cached (default 24h) to control API cost.
3. **Score** — `scoring.score_vehicle()` produces a 0–100 risk score with
   human-readable drivers and the accruing floor-plan cost.
4. **Recommend** — `recommend.build_recommendation()` combines the score with
   a market-anchored price (`pricing.recommend_price`) and a marketing action.
5. **Track** — `tracker.track_vehicle()` places each unit on the
   30/45/60/75/90 milestone ladder and detects newly-crossed milestones.
6. **Alert** — `alerts.dispatch_alerts()` sends digests via SendGrid / Twilio.
   `scheduler.run_once()` ties this together for a daily cron.

## Why the engines are separate modules

Each engine (`scoring`, `pricing`, `tracker`) is pure and independently
testable — no I/O, no framework coupling. The API and scheduler are thin
orchestration layers on top. This keeps the business logic portable: it can
run in a Lambda, a cron job, or behind the API without change, and the test
suite exercises the logic directly.

## Graceful degradation

The system is designed to produce useful output even with minimal data:

| Available data | Pricing behavior | Confidence label |
|----------------|------------------|------------------|
| Market comps present | Anchor to market, shift by age | `MARKET-BACKED` |
| No market comps | Age-based cut from current price | `AGE-BASED` |

A MarketCheck outage or missing key never breaks the pipeline — the adapter
returns `(None, None)` and scoring leans on age + demand signals.

## Deployment options

**Single host (Docker Compose).** `docker compose up --build` runs backend,
frontend (nginx), and optionally the scheduler. Good for a pilot or a single
dealer group.

**Managed/serverless.** The backend is a standard ASGI app — deploy to any
container platform (Cloud Run, ECS, Fly, Render). The frontend `dist/` is
static and can go on any CDN/static host. Point `VITE_API_BASE` at the
backend URL at build time.

**Scheduler.** Either the commented `scheduler` service in
`docker-compose.yml`, a host cron entry (`0 7 * * * python -m app.scheduler`),
or a platform scheduled task.

## Production hardening checklist

This repo is a working MVP. Before serving real dealers:

- Add a database (Postgres) for dealers, vehicles, and a milestone-state table
  so "newly crossed" is tracked from stored state instead of an assumed
  `days_since_last_check`.
- Add authentication (API keys per dealer) and rate limiting.
- Persist the MarketCheck cache (Redis) instead of in-process memory.
- Add structured logging and error monitoring.
- Confirm MarketCheck licensing permits resale inside a product served to
  third-party dealers.

## Tuning

Business assumptions live in `config.py` and `scoring.py`:
`FLOORPLAN_APR`, `TARGET_TURN_DAYS`, milestone days, and the scoring weights.
In a multi-dealer deployment these should move to per-dealer settings in the
database.
