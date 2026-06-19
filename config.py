"""
Configuration. All values are read from environment variables so the
same image runs in dev, staging, and prod without code changes.
"""

import os


class Settings:
    APP_NAME = "Aging Inventory Agent"
    VERSION = "1.0.0"

    # Business defaults (overridable per dealer in a real DB)
    FLOORPLAN_APR = float(os.getenv("FLOORPLAN_APR", "0.085"))
    TARGET_TURN_DAYS = int(os.getenv("TARGET_TURN_DAYS", "45"))

    # MarketCheck (optional — engine degrades gracefully if unset)
    MARKETCHECK_API_KEY = os.getenv("MARKETCHECK_API_KEY", "")
    MARKETCHECK_BASE_URL = os.getenv(
        "MARKETCHECK_BASE_URL", "https://mc-api.marketcheck.com/v2"
    )
    MARKET_CACHE_TTL_HOURS = int(os.getenv("MARKET_CACHE_TTL_HOURS", "24"))

    # Alerts
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    ALERT_FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", "alerts@example.com")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

    # CORS — comma-separated list of allowed frontend origins
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


settings = Settings()
