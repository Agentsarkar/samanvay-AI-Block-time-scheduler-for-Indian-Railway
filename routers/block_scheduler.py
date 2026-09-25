import os
import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import services.block_scheduler as _bs

from config import get_sim_day_correct

router = APIRouter(prefix="/api/block-scheduler", tags=["Maintenance Block Scheduler"])

class SubmitDecisionRequest(BaseModel):
    block_id: str
    corridor_id: str
    fault_ids: list
    category: str
    block_start: str
    block_end: str
    block_dur_min: int
    day_of_week: str
    window_type: str
    ai_recommendation: Optional[str] = ""
    ai_feasibility: Optional[str] = "UNKNOWN"
    manager_decision: str
    manager_notes: Optional[str] = ""

ACTIVE_ADVISORY_STATE: Dict[str, Any] = {}

def get_default_advisory() -> Dict[str, Any]:
    try:
        merge_res = _bs.merge_faults(["TMS-042", "TDMS-11"])
        c0 = (merge_res.get("clusters") or merge_res.get("standalone") or [{}])[0]
        req_dur = c0.get("block_duration_min", 90)
        time_saved = c0.get("time_saved_min", 30)
        ind_durs = c0.get("individual_durations", [60, 60])
        ind_sum = sum(ind_durs) if ind_durs else (req_dur + time_saved)
        eff_pct = round((time_saved / ind_sum) * 100) if ind_sum > 0 else 25

        impact = _bs.score_window_impact("hwh_bwn_main", "tuesday", 200, 255, req_dur)
        aff_trains = impact.get("affected_trains", [])

        return {
            "corridor_id": "hwh_bwn_main",
            "corridor_name": "Howrah - Barddhaman Main Line",
            "cluster_id": c0.get("cluster_id", "CLU-01"),
            "fault_count": c0.get("fault_count", 2),
            "faults": c0.get("faults", [
                {"id": "TMS-042", "category": "Track", "required_min": 60, "location_name": "Between Bandel Jn and Adi Saptagram (KM 108/4)"},
                {"id": "TDMS-11", "category": "Traction", "required_min": 60, "location_name": "Between Memari & Rasulpur"}
            ]),
            "requested_block_min": req_dur,
            "time_saved_min": time_saved,
            "individual_durations": ind_durs,
            "efficiency_pct": eff_pct,
            "window_day": "tuesday",
            "window_start": "03:20",
            "window_end": "04:15",
            "available_gap_min": 55,
            "headroom_min": 0,
            "affected_trains": aff_trains,
            "affected_train_count": len(aff_trains),
            "total_penalty_score": impact.get("total_penalty_score", 365),
            "is_approved": False,
        }
    except Exception as e:
        return {
            "corridor_id": "hwh_bwn_main",
            "corridor_name": "Howrah - Barddhaman Main Line",
            "cluster_id": "CLU-01",
            "fault_count": 2,
            "faults": [
                {"id": "TMS-042", "category": "Track", "required_min": 60, "location_name": "Between Bandel Jn and Adi Saptagram (KM 108/4)"},
                {"id": "TDMS-11", "category": "Traction", "required_min": 60, "location_name": "Between Memari & Rasulpur"}
            ],
            "requested_block_min": 90,
            "time_saved_min": 30,
            "individual_durations": [60, 60],
            "efficiency_pct": 25,
            "window_day": "tuesday",
            "window_start": "03:20",
            "window_end": "04:15",
            "available_gap_min": 55,
            "headroom_min": 0,
            "affected_trains": [
                {"train_number": "13027", "train_name": "Azimganj Kaviguru Express"},
                {"train_number": "13022", "train_name": "Mithila Express"},
                {"train_number": "37812", "train_name": "Barddhaman - Howrah Local"},
                {"train_number": "13030", "train_name": "Mokama - Howrah Express"}
            ],
            "affected_train_count": 4,
            "total_penalty_score": 365,
            "is_approved": False,
        }

@router.get("/active-advisory")
def api_get_active_advisory():
    global ACTIVE_ADVISORY_STATE
    if not ACTIVE_ADVISORY_STATE:
        ACTIVE_ADVISORY_STATE = get_default_advisory()
    return JSONResponse(content=ACTIVE_ADVISORY_STATE, headers={"Cache-Control": "no-cache"})

@router.post("/active-advisory")
def api_post_active_advisory(req_data: Dict[str, Any]):
    global ACTIVE_ADVISORY_STATE
    if not ACTIVE_ADVISORY_STATE:
        ACTIVE_ADVISORY_STATE = get_default_advisory()
    ACTIVE_ADVISORY_STATE.update(req_data)
    return JSONResponse(content={"success": True, "active_advisory": ACTIVE_ADVISORY_STATE})

@router.post("/submit-decision")
async def api_bs_submit_decision(req: SubmitDecisionRequest):
    try:
        _bs.save_manager_decision(
            block_id=req.block_id,
            corridor_id=req.corridor_id,
            fault_ids=req.fault_ids,
            category=req.category,
            block_start=req.block_start,
            block_end=req.block_end,
            block_dur_min=req.block_dur_min,
            day_of_week=req.day_of_week,
            window_type=req.window_type,
            ai_recommendation=req.ai_recommendation or "",
            ai_feasibility=req.ai_feasibility or "UNKNOWN",
            manager_decision=req.manager_decision,
            manager_notes=req.manager_notes or "",
        )
        return {"success": True, "block_id": req.block_id, "decision": req.manager_decision}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedule")
async def api_bs_schedule(corridor_id: Optional[str] = None):
    blocks = _bs.load_scheduled_blocks(corridor_id)
    return JSONResponse(content={"blocks": blocks, "count": len(blocks)}, headers={"Cache-Control": "no-cache"})

@router.get("/next-best")
async def api_bs_next_best(
    corridor_id: str,
    block_duration_min: int,
    current_day: Optional[str] = None,
    current_start: Optional[int] = None,
):
    generic_week = _bs.find_free_windows_all_days(corridor_id, block_duration_min)
    candidates = []
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for day in days:
        dv = generic_week["week"][day]
        for gap in dv["feasible_gaps"]:
            if current_day and current_start:
                if day == current_day and abs(gap["gap_start_min"] - current_start) < 30:
                    continue
            impact = _bs.score_window_impact(
                corridor_id, day, gap["gap_start_min"], gap["gap_end_min"]
            )
            candidates.append({
                "day": day,
                "gap_start": gap["gap_start"],
                "gap_end": gap["gap_end"],
                "gap_start_min": gap["gap_start_min"],
                "gap_end_min": gap["gap_end_min"],
                "gap_duration_min": gap["gap_duration_min"],
                "headroom_min": gap["headroom_min"],
                "total_penalty_score": impact["total_penalty_score"],
                "affected_train_count": impact["affected_train_count"],
            })
    candidates.sort(key=lambda x: (x["total_penalty_score"], -x["headroom_min"]))
    return JSONResponse(content={"next_best": candidates[:3]}, headers={"Cache-Control": "no-cache"})
