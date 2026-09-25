import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.dbscan_clustering import run_dbscan
from services.nsga2_optimizer import run_nsga2
from services.gap_calculator import load_trains_from_db, calculate_all_gap_schedules

from config import BASE_DIR, get_data_file, get_sim_day_correct

router = APIRouter(prefix="/api", tags=["Optimization & Clustering Engines"])

@router.get("/cluster-faults")
def api_cluster_faults():
    try:
        faults_path = str(get_data_file("faults.json"))
        clusters = run_dbscan(faults_path)
        return JSONResponse({"clusters": clusters})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/nsga2-optimize")
def api_nsga2_optimize():
    try:
        faults_path = str(get_data_file("faults.json"))
        clusters = run_dbscan(faults_path)
        trains = load_trains_from_db()
        day_short = get_sim_day_correct()
        results = run_nsga2(clusters, trains, day_short, pop_size=30, max_gen=20)
        return JSONResponse({"options": results})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/timetable-gaps")
def get_timetable_gaps():
    gap_file = get_data_file("gap_schedules.json")
    if not gap_file.exists():
        try:
            calculate_all_gap_schedules()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate gap schedules: {e}")
    try:
        import json
        with open(gap_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data, headers={"Cache-Control": "no-cache"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read gap schedules: {e}")
