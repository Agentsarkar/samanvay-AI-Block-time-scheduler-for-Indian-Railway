from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from config import get_data_file

router = APIRouter(prefix="/api", tags=["GIS Live Map & Network Infrastructure"])

@router.get("/faults")
async def get_faults():
    faults_file = get_data_file("faults.json")
    if faults_file.exists():
        return FileResponse(str(faults_file), media_type="application/json", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {"corridor": "Howrah - Barddhaman", "faults": []}

@router.get("/network")
async def get_network():
    net_file = get_data_file("corridor_network.json")
    if net_file.exists():
        return FileResponse(str(net_file), media_type="application/json", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    raise HTTPException(status_code=404, detail="Network data not found")

@router.get("/stations")
async def get_stations():
    stations_file = get_data_file("all_stations.json")
    if stations_file.exists():
        return FileResponse(str(stations_file), media_type="application/json", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    raise HTTPException(status_code=404, detail="Stations data not found")
