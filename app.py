"""
================================================================================
SAMANVAY — Strategic Maintenance Decision Support System (FastAPI Core Server)
Modular Feature Architecture for Parallel Team Collaboration
================================================================================
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import BASE_DIR, get_template_file
from routers import auth, map as map_router, block_scheduler, degradation, optimization
from plugin_loader import register_plugins

app = FastAPI(
    title="SAMANVAY - Railway DSS Backend",
    description="Modular Decision Support System for Indian Railways Maintenance & Scheduling",
    version="2.0.0"
)

# ── 1. Static Files Mounting ──
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ── 2. Include Core Feature Routers ──
app.include_router(auth.router)
app.include_router(map_router.router)
app.include_router(block_scheduler.router)
app.include_router(degradation.router)
app.include_router(optimization.router)

# ── 3. Auto-Register Teammate Feature Plugins ──
print("\n[SYSTEM] Loading Team Feature Plugins...")
registered_team_plugins = register_plugins(app)
print(f"[SYSTEM] Total Active Team Plugins: {len(registered_team_plugins)}\n")

# ── 4. Serve Page HTML Routes from templates/ folder ──
@app.get("/railway.jpg")
async def get_railway_image():
    img_path = BASE_DIR / "railway.jpg"
    if img_path.exists():
        return FileResponse(str(img_path), media_type="image/jpeg")
    return FileResponse(str(BASE_DIR / "static" / "railway.jpg"))

@app.get("/", response_class=FileResponse)
@app.get("/index.html", response_class=FileResponse)
async def serve_index():
    return FileResponse(str(get_template_file("index.html")))

@app.get("/login", response_class=FileResponse)
@app.get("/login.html", response_class=FileResponse)
async def serve_login():
    return FileResponse(str(get_template_file("login.html")))

@app.get("/map", response_class=FileResponse)
@app.get("/map.html", response_class=FileResponse)
async def serve_map():
    return FileResponse(str(get_template_file("map.html")), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/block", response_class=FileResponse)
@app.get("/block.html", response_class=FileResponse)
async def serve_block():
    return FileResponse(str(get_template_file("block.html")), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/degradation", response_class=FileResponse)
@app.get("/degradation.html", response_class=FileResponse)
async def serve_degradation():
    return FileResponse(str(get_template_file("degradation.html")), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


# ── 5. Main Startup Execution ──
if __name__ == "__main__":
    import uvicorn
    print("=======================================================")
    print("  SAMANVAY - Strategic Maintenance Decision Support System")
    print("  Modular Team Architecture running at: http://127.0.0.1:8000")
    print("  Login Page:        http://127.0.0.1:8000/login.html")
    print("  Dashboard:         http://127.0.0.1:8000/index.html")
    print("  GIS Live Map:      http://127.0.0.1:8000/map.html")
    print("  Block Scheduler:   http://127.0.0.1:8000/block.html")
    print("  Degradation Sim:   http://127.0.0.1:8000/degradation.html")
    print("  Interactive Docs:  http://127.0.0.1:8000/docs")
    print("=======================================================\n")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
