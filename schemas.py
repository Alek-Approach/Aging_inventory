"""Pydantic models shared across the API."""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class VehicleIn(BaseModel):
    vin: str
    year: int
    make: str
    model: str
    cost: float = Field(..., description="Floor-planned / acquisition cost")
    list_price: float
    date_in_stock: date
    photos_count: int = 0
    leads_30d: int = 0
    views_30d: int = 0
    market_avg_price: Optional[float] = None
    market_days_supply: Optional[int] = None


class AnalyzeRequest(BaseModel):
    vehicles: List[VehicleIn]
    floorplan_apr: float = 0.085


class TrackRequest(BaseModel):
    vehicles: List[VehicleIn]
    days_since_last_check: int = Field(
        1, description="Days since the dealer last uploaded; controls which milestone alerts are 'new'."
    )


class HealthResponse(BaseModel):
    status: str
    version: str
