# # backend/main.py
# # to run: python -m uvicorn backend.main:app --reload


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from backend.routes import analyze, auth, community, reports
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

@app.get("/")
def root():
    return {"message": "API Running"}
    
if __name__ == "__main__":
        import uvicorn
        import os
        port = int(os.environ.get("PORT", 10000))
        uvicorn.run(app, host="0.0.0.0", port=port)
   
