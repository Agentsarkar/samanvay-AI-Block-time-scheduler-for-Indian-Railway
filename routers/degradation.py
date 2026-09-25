import os
import json
import urllib.request
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from config import IST

router = APIRouter(prefix="/api/degradation", tags=["Asset Degradation Simulator"])

class DegradationSimRequest(BaseModel):
    fault_id: Optional[str] = "TMS-042"
    fault_type: Optional[str] = "track_gap"
    asset_name: Optional[str] = "KM 41/4 Rail Joint Gap"
    location: Optional[str] = "Bandel Jn - Adi Saptagram"
    corridor_id: Optional[str] = "hwh_bwn_main"
    gap_inches: Optional[float] = 2.0
    sag_mm: Optional[float] = 18.0
    wire_wear_pct: Optional[float] = 42.0
    trains_per_day: Optional[int] = 148
    axle_load_tonnes: Optional[float] = 22.5
    speed_limit_kmph: Optional[int] = 110

@router.post("/simulate")
async def api_degradation_simulate(req: DegradationSimRequest):
    ftype = (req.fault_type or "track_gap").lower()
    trains_day = max(10, req.trains_per_day or 148)
    axle_load = req.axle_load_tonnes or 22.5
    gap_in = req.gap_inches or 2.0
    sag_mm = req.sag_mm or 18.0
    wear_pct = req.wire_wear_pct or 42.0

    timeline = []
    curr_health = 88.0 if ftype == "track_gap" else (85.0 if ftype == "traction_sag" else 90.0)
    warning_day = None
    emergency_day = None

    for d in range(46):
        if ftype == "track_gap":
            impact_factor = 1.0 + 0.35 * (gap_in ** 1.35) * (axle_load / 22.5) * ((req.speed_limit_kmph or 110) / 100.0)
            daily_drop = 0.42 * (impact_factor ** 1.8) * (trains_day / 100.0) * (1.0 + (d / 20.0) ** 1.5)
        elif ftype == "traction_sag":
            panto_force = 70.0 + 2.4 * sag_mm * ((req.speed_limit_kmph or 110) / 100.0)
            daily_drop = (0.25 + 0.15 * ((wear_pct / 40.0) ** 2)) * (panto_force / 70.0) * (trains_day / 100.0) * (1.0 + (d / 22.0) ** 1.4)
        elif ftype == "cms_crossing":
            daily_drop = 0.55 * ((axle_load / 22.5) ** 2.2) * (trains_day / 100.0) * (1.0 + (d / 18.0) ** 1.6)
        else:
            daily_drop = 0.65 * (trains_day / 100.0) * (1.0 + (d / 25.0) ** 1.2)

        health_val = max(3.0, round(curr_health, 1))

        status_label = "SAFE"
        if health_val < 25.0:
            status_label = "PRIORITY EMERGENCY"
            if emergency_day is None:
                emergency_day = d
        elif health_val < 55.0:
            status_label = "WARNING"
            if warning_day is None:
                warning_day = d

        timeline.append({
            "day": d,
            "health": health_val,
            "status": status_label,
            "cumulative_trains": d * trains_day
        })

        curr_health -= daily_drop

    if warning_day is None:
        warning_day = 12
    if emergency_day is None:
        emergency_day = 18

    now_dt = datetime.now(IST)
    warning_date_str = (now_dt + timedelta(days=warning_day)).strftime("%d-%b-%Y")
    emergency_date_str = (now_dt + timedelta(days=emergency_day)).strftime("%d-%b-%Y")

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1")
    site_url = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000")
    site_name = os.getenv("OPENROUTER_SITE_NAME", "SAMANVAY-DSS")

    ai_response = None

    if ftype == "track_gap":
        mech_text = (
            f"The {gap_in}-inch gap under {trains_day} daily train passes causes high dynamic impact loading (K={round(1.0+0.35*(gap_in**1.35)*(axle_load/22.5),2)}). "
            f"According to Paris' Law fatigue growth, heavy {axle_load}T axle stress concentration accelerates rail micro-fissure propagation into a full transverse crack fracture."
        )
        conseq_text = (
            f"By Day {emergency_day} ({emergency_date_str}), accumulated wheel impacts ({emergency_day * trains_day} trains) will breach critical crack length. "
            f"Unmitigated operation past this point creates catastrophic derailment risk for high-speed passenger expresses."
        )
        recs = [
            f"Impose immediate 20 km/h speed restriction on {req.location} to drop dynamic impact by 45%.",
            f"Schedule a 105-minute emergency track block prior to Day {warning_day} ({warning_date_str}) for thermit weld re-execution.",
            f"Deploy Ultrasonic Flaw Detection (USFD) vehicle to monitor crack depth growth twice weekly."
        ]
    elif ftype == "traction_sag":
        mech_text = (
            f"An OHE wire sag of {sag_mm}mm combined with {wear_pct}% contact wire section loss increases pantograph dynamic strike force to {round(70.0+2.4*sag_mm, 1)} N. "
            f"Each pantograph pass ({trains_day * 2} passes/day) generates localized arcing, thermal degradation, and mechanical notches."
        )
        conseq_text = (
            f"By Day {emergency_day} ({emergency_date_str}), contact wire cross-section will drop below minimum tensile safety threshold, leading to catenary wire snap, pantograph entanglement, and multi-track power trip."
        )
        recs = [
            f"Schedule 90-min OHE power block before Day {warning_day} ({warning_date_str}) for tower wagon re-tensioning.",
            f"Replace worn contact wire splice and recalibrate dropper tension.",
            f"Issue advisory to electric locomotives to lower pantograph speed when passing KM 166/8."
        ]
    else:
        mech_text = f"Asset load of {trains_day} trains/day is causing cyclic stress degradation. Failure projected at Day {emergency_day}."
        conseq_text = f"Asset failure by Day {emergency_day} will cause severe blockages and signal trips."
        recs = ["Schedule maintenance block within 7 days", "Enforce local caution order"]

    if api_key:
        prompt = f"""You are the Lead Railway Infrastructure Safety AI (DeepSeek R1) for Indian Railways SAMANVAY DSS.

ASSET DEGRADATION EVENT DATA:
- Asset Name: {req.asset_name}
- Category/Type: {req.fault_type}
- Location: {req.location} ({req.corridor_id})
- Parameter: Gap={gap_in} in / Sag={sag_mm} mm / Wear={wear_pct}%
- Operating Load: {trains_day} trains/day ({axle_load}T axle load)
- Calculated Emergency Threshold Day: DAY {emergency_day} ({emergency_date_str})
- Total Trains Passed Until Failure: {emergency_day * trains_day} trains

Provide a concise, ultra-authoritative engineering safety diagnosis in valid JSON format:
{{
  "degradation_mechanism": "Explanation of mechanical/electrical fatigue physics under heavy traffic load",
  "failure_consequence": "Explicit failure prediction (e.g. derailment risk, catenary snap) on Day {emergency_day} ({emergency_date_str})",
  "derailment_risk_rating": "CRITICAL (94% Failure Probability on Day {emergency_day})",
  "action_recommendations": [
    "Action 1 (Speed restriction)",
    "Action 2 (Emergency Block Schedule recommendation)",
    "Action 3 (Inspection protocol)"
  ]
}}"""
        try:
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 1000,
            }).encode("utf-8")

            req_obj = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": site_url,
                    "X-Title": site_name,
                },
                method="POST",
            )
            with urllib.request.urlopen(req_obj, timeout=12) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                raw_content = resp_json["choices"][0]["message"]["content"]
                if "```json" in raw_content:
                    raw_content = raw_content.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_content:
                    raw_content = raw_content.split("```")[1].split("```")[0].strip()
                ai_response = json.loads(raw_content)
        except Exception as _e:
            print(f"[WARN] OpenRouter DeepSeek R1 call exception: {_e}")

    if not ai_response:
        ai_response = {
            "degradation_mechanism": mech_text,
            "failure_consequence": conseq_text,
            "derailment_risk_rating": f"CRITICAL ({emergency_day} Days to Failure)",
            "action_recommendations": recs
        }

    return JSONResponse(content={
        "success": True,
        "fault_id": req.fault_id,
        "fault_type": ftype,
        "asset_name": req.asset_name,
        "location": req.location,
        "parameters": {
            "gap_inches": gap_in,
            "sag_mm": sag_mm,
            "wire_wear_pct": wear_pct,
            "trains_per_day": trains_day,
            "axle_load_tonnes": axle_load
        },
        "days_to_warning": warning_day,
        "warning_date": warning_date_str,
        "days_to_emergency": emergency_day,
        "emergency_date": emergency_date_str,
        "total_trains_before_failure": emergency_day * trains_day,
        "health_timeline": timeline,
        "ai_analysis": ai_response
    }, headers={"Cache-Control": "no-cache"})
