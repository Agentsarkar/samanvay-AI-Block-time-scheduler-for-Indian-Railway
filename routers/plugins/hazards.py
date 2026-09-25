"""
SAMANVAY Feature Plugin: Real-Time Hazard Alerts
Teammate working on Hazards (e.g. Obstruction, Flooding, Trespassing, Animal Crossing) can edit this file independently!
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/hazards", tags=["Plugin: Real-Time Hazard Monitoring"])

@router.get("/active")
async def get_active_hazards(corridor_id: str = "hwh_bwn_main"):
    """
    Returns active real-time track hazards (e.g., Waterlogging, Fallen Tree, Cattle Crossing).
    """
    return JSONResponse(content={
        "corridor_id": corridor_id,
        "total_hazards": 1,
        "hazards": [
            {
                "hazard_id": "HAZ-2026-04",
                "type": "TRACK_WATERLOGGING",
                "severity": "MODERATE",
                "location": "KM 52/12 (Memari Yard)",
                "lat": 23.1812,
                "long": 88.1145,
                "detected_at": "2026-09-25 15:30 IST",
                "caution_order_kmph": 30,
                "status": "MONITORING"
            }
        ]
    })
