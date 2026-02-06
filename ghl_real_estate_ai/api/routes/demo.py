"""Demo routes — hardcoded sample data for zero-config API exploration.

No authentication required. Provides realistic Rancho Cucamonga real estate
data so evaluators can explore the Swagger UI at /docs immediately.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from random import Random

from fastapi import APIRouter

router = APIRouter(prefix="/demo", tags=["Demo"])

# Seeded RNG for deterministic sample data
_rng = Random(42)

_FIRST_NAMES = ["Maria", "James", "Sofia", "Robert", "Ana", "David", "Carmen", "Michael", "Elena", "John"]
_LAST_NAMES = ["Garcia", "Johnson", "Martinez", "Williams", "Rodriguez", "Brown", "Lopez", "Davis", "Hernandez", "Smith"]
_STREETS = [
    "Haven Ave", "Foothill Blvd", "Baseline Rd", "Archibald Ave",
    "Milliken Ave", "Rochester Ave", "Etiwanda Ave", "Day Creek Blvd",
    "Banyan St", "Church St",
]
_SOURCES = ["Zillow", "Realtor.com", "Facebook Ad", "Google Ad", "Referral", "Open House", "Walk-In", "GHL Form"]
_TEMPERATURES = ["Hot-Lead", "Warm-Lead", "Cold-Lead"]
_STAGES = ["New", "Contacted", "Qualified", "Showing Scheduled", "Offer Submitted", "Under Contract", "Closed"]


def _generate_leads() -> list[dict]:
    now = datetime.now()
    leads = []
    for i in range(10):
        first = _FIRST_NAMES[i]
        last = _LAST_NAMES[i]
        score = _rng.randint(15, 98)
        temp = "Hot-Lead" if score >= 80 else "Warm-Lead" if score >= 40 else "Cold-Lead"
        leads.append({
            "id": f"lead_{i + 1:03d}",
            "first_name": first,
            "last_name": last,
            "email": f"{first.lower()}.{last.lower()}@example.com",
            "phone": f"+1909{_rng.randint(1000000, 9999999)}",
            "source": _SOURCES[i % len(_SOURCES)],
            "score": score,
            "temperature": temp,
            "stage": _STAGES[min(i, len(_STAGES) - 1)],
            "budget_min": _rng.randint(400, 700) * 1000,
            "budget_max": _rng.randint(700, 1200) * 1000,
            "bedrooms": _rng.choice([3, 4, 5]),
            "address_interest": f"{_rng.randint(1000, 9999)} {_STREETS[i]}",
            "city": "Rancho Cucamonga",
            "created_at": (now - timedelta(days=_rng.randint(1, 30))).isoformat(),
            "last_activity": (now - timedelta(hours=_rng.randint(1, 72))).isoformat(),
        })
    return leads


def _generate_pipeline() -> dict:
    return {
        "snapshot_at": datetime.now().isoformat(),
        "stages": {
            "New": {"count": 12, "avg_score": 45, "avg_days_in_stage": 1.2},
            "Contacted": {"count": 8, "avg_score": 52, "avg_days_in_stage": 2.5},
            "Qualified": {"count": 6, "avg_score": 68, "avg_days_in_stage": 4.1},
            "Showing Scheduled": {"count": 4, "avg_score": 74, "avg_days_in_stage": 3.8},
            "Offer Submitted": {"count": 3, "avg_score": 82, "avg_days_in_stage": 5.2},
            "Under Contract": {"count": 2, "avg_score": 88, "avg_days_in_stage": 12.0},
            "Closed": {"count": 5, "avg_score": 91, "avg_days_in_stage": 0.0},
        },
        "summary": {
            "total_leads": 40,
            "conversion_rate": 0.125,
            "avg_days_to_close": 28.5,
            "pipeline_value": 4_250_000,
            "temperature_distribution": {
                "Hot-Lead": 8,
                "Warm-Lead": 18,
                "Cold-Lead": 14,
            },
        },
    }


_LEADS = _generate_leads()
_PIPELINE = _generate_pipeline()


@router.get("/leads")
async def demo_leads():
    """10 sample leads with realistic Rancho Cucamonga data. No auth required."""
    return {"leads": _LEADS, "total": len(_LEADS)}


@router.get("/pipeline")
async def demo_pipeline():
    """Sample pipeline snapshot showing lead flow across stages. No auth required."""
    return _PIPELINE
