import secrets
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from config import BASE_DIR, USERS_FILE

router = APIRouter(prefix="/api", tags=["Authentication & User Management"])

# Session store: session_token -> user_dict
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

DEFAULT_USERS = {
    "7842901": {
        "employee_id": "7842901",
        "password": "railway@123",
        "name": "Rajesh Sharma",
        "role_id": "maintenance-planner",
        "role_title": "Divisional Engineer (Eastern Railway)",
        "division": "Howrah",
        "section": "HWH–BWN Main Line",
    },
    "7842902": {
        "employee_id": "7842902",
        "password": "railway@123",
        "name": "Priya Mukherjee",
        "role_id": "control-room",
        "role_title": "Control Room Dispatcher (Live DSS)",
        "division": "Howrah",
        "section": "HWH–BWN Main Line",
    },
    "7842903": {
        "employee_id": "7842903",
        "password": "railway@123",
        "name": "Amitav Sen",
        "role_id": "maintenance-planner",
        "role_title": "Senior Divisional Engineer (Coordination)",
        "division": "Sealdah",
        "section": "SDAH–RHA Line",
    },
    "admin": {
        "employee_id": "admin",
        "password": "admin123",
        "name": "Er. V. K. Verma",
        "role_id": "maintenance-planner",
        "role_title": "Divisional Engineer (Eastern Railway)",
        "division": "Howrah",
        "section": "HWH–BWN Main Line",
    },
}

def load_users() -> Dict[str, Dict[str, Any]]:
    users = dict(DEFAULT_USERS)
    if not USERS_FILE.exists():
        return users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(":")]
                if len(parts) >= 5:
                    emp_id = parts[0]
                    users[emp_id] = {
                        "employee_id": emp_id,
                        "password": parts[1],
                        "name": parts[2],
                        "role_id": parts[3],
                        "role_title": parts[4],
                        "division": parts[5] if len(parts) > 5 else "Howrah",
                        "section": parts[6] if len(parts) > 6 else "HWH–BWN Main Line",
                    }
    except Exception as e:
        print(f"[WARN] Failed reading users.txt: {e}. Using fallback credentials.")
    return users

class LoginRequest(BaseModel):
    employeeId: str
    password: str
    role: Optional[str] = None
    captcha: Optional[str] = None

def get_current_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get("samanvay_session")
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]
    if token and token in ACTIVE_SESSIONS:
        return ACTIVE_SESSIONS[token]
    return None

@router.get("/users")
async def get_available_users():
    users = load_users()
    demo_list = []
    for u in users.values():
        demo_list.append({
            "employeeId": u["employee_id"],
            "name": u["name"],
            "roleId": u["role_id"],
            "roleTitle": u["role_title"],
            "division": u["division"]
        })
    return {"users": demo_list}

@router.post("/login")
async def api_login(req: LoginRequest, response: Response):
    users = load_users()
    emp_id = req.employeeId.strip()
    pwd = req.password.strip()

    if req.captcha is not None:
        captcha_clean = req.captcha.strip().replace(" ", "").upper()
        if captcha_clean not in ["RAIL7842", "7842"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "Invalid Security Verification (CAPTCHA). Expected 'RAIL 7842'."}
            )

    if emp_id not in users:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": f"Employee ID '{emp_id}' not found in railway directory."}
        )

    user = users[emp_id]
    if user["password"] != pwd:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "Incorrect password. Please verify your credentials."}
        )

    selected_role = (req.role or "").strip()
    if selected_role and selected_role != user["role_id"]:
        expected_name = "Maintenance Planner" if user["role_id"] == "maintenance-planner" else "Control Room Dispatcher"
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": f"Authorization mismatch: {user['name']} is designated for the '{expected_name}' module."
            }
        )

    session_token = secrets.token_hex(24)
    ACTIVE_SESSIONS[session_token] = {
        "employeeId": user["employee_id"],
        "name": user["name"],
        "roleId": user["role_id"],
        "roleTitle": user["role_title"],
        "division": user["division"],
        "section": user["section"],
    }

    response.set_cookie(
        key="samanvay_session",
        value=session_token,
        httponly=False,
        max_age=86400,
        samesite="lax"
    )

    return {
        "success": True,
        "token": session_token,
        "user": ACTIVE_SESSIONS[session_token],
        "redirect": "/index.html"
    }

@router.get("/me")
async def api_me(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"authenticated": False, "message": "No active session"}
        )
    return {"authenticated": True, "user": user}

@router.post("/logout")
async def api_logout(request: Request, response: Response):
    token = request.cookies.get("samanvay_session")
    if token and token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]
    response.delete_cookie("samanvay_session")
    return {"success": True, "message": "Logged out successfully"}
