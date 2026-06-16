# backend/main.py
# Run: uvicorn backend.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.routes import analyze, auth, community, reports, domains, user
from backend.admin import routes as admin_routes

app = FastAPI(title="ScamShield API")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# ── CORS (allow all for local dev) ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ──────────────────────────────────────────────
app.include_router(auth.router,         prefix="/api")
app.include_router(community.router,    prefix="/api")
app.include_router(reports.router,      prefix="/api")
app.include_router(admin_routes.router, prefix="/api")
app.include_router(analyze.router,      prefix="/api")
app.include_router(domains.router,      prefix="/api")
app.include_router(user.router,         prefix="/api")

# ── Startup: seed demo accounts ─────────────────────────────
@app.on_event("startup")
async def startup_event():
    try:
        from backend.supabase_client import supabase
        from backend.auth import hash_password
        from datetime import datetime, timezone

        DEMO = [
            {"email": "admin@scamshield.in", "password": "Admin@2026", "name": "ScamShield Admin", "role": "admin"},
            {"email": "demo@scamshield.in",  "password": "Demo@2026",  "name": "Demo User",         "role": "user"},
        ]
        for acc in DEMO:
            existing = supabase.table("admin_users").select("id").eq("email", acc["email"]).execute()
            if not existing.data:
                supabase.table("admin_users").insert({
                    "name":          acc["name"],
                    "email":         acc["email"],
                    "password_hash": hash_password(acc["password"]),
                    "role":          acc["role"],
                    "created_at":    datetime.now(timezone.utc).isoformat(),
                }).execute()
                print(f"[seed] Created demo account: {acc['email']}")
            else:
                print(f"[seed] OK: {acc['email']}")
    except Exception as e:
        print(f"[seed] Warning: {e}")

# ── Static frontend ──────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "API Running"}
    
if __name__ == "__main__":
        import uvicorn
        import os
        port = int(os.environ.get("PORT", 10000))
        uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
   
