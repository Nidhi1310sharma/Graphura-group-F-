# # backend/main.py
# # to run: python -m uvicorn backend.main:app --reload


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from backend.routes import analyze, auth, community, reports, domains
from backend.admin import routes

app = FastAPI()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(routes.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(domains.router, prefix="/api")

# frontend routes
@app.get("/")
async def serve_home():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/{file_path:path}")
async def serve_frontend(file_path: str):
    file = FRONTEND_DIR / file_path

    if file.exists() and file.is_file():
        return FileResponse(file)

    return FileResponse(FRONTEND_DIR / "index.html")

