from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import date

class CMAProperty(BaseModel):
    address: str
    beds: int
    baths: float
    sqft: int
    year_built: int
    condition: str
    updates: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)

class Comparable(BaseModel):
    address: str
    sale_date: date
    sale_price: float
    sqft: int
    beds: int
    baths: float
    price_per_sqft: float
    adjustment_percent: float = 0.0
    adjusted_value: float = 0.0

class MarketContext(BaseModel):
    market_name: str = "Austin, TX"
    price_trend: float  # Percentage
    dom_average: int
    inventory_level: int
    zillow_zestimate: float

class CMAReport(BaseModel):
    subject_property: CMAProperty
    comparables: List[Comparable]
    market_context: MarketContext
    
    # Analysis Results
    estimated_value: float
    value_range_low: float
    value_range_high: float
    confidence_score: int
    
    # Zillow Defense
    zillow_variance_abs: float
    zillow_variance_percent: float
    zillow_explanation: str
    
    # Narrative
    market_narrative: str
    generated_at: date = Field(default_factory=date.today)
