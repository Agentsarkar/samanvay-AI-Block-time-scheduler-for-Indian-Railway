"""
SAMANVAY Feature Plugin: Weather Integration
Teammate working on Weather features can edit this file independently!
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/weather", tags=["Plugin: Real-Time Weather Integration"])

@router.get("/current")
async def get_corridor_weather(corridor_id: str = "hwh_bwn_main"):
    """
    Returns live weather & visibility metrics for a railway corridor section.
    """
    return JSONResponse(content={
        "status": "ACTIVE",
        "corridor_id": corridor_id,
        "temperature_celsius": 29.5,
        "humidity_pct": 78,
        "rainfall_mm_hr": 0.0,
        "visibility_meters": 3500,
        "fog_alert": False,
        "speed_impact": "NORMAL"
    })

@router.get("/forecast")
async def get_weather_forecast(corridor_id: str = "hwh_bwn_main"):
    """
    Returns 24-hour weather forecast for maintenance block planning.
    """
    return JSONResponse(content={
        "corridor_id": corridor_id,
        "forecast": [
            {"hour": "06:00", "condition": "Clear", "rain_prob_pct": 10},
            {"hour": "12:00", "condition": "Partly Cloudy", "rain_prob_pct": 20},
            {"hour": "18:00", "condition": "Light Rain", "rain_prob_pct": 60}
        ]
    })
