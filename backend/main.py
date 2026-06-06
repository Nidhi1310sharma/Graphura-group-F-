# # backend/main.py
# # to run: python -m uvicorn backend.main:app --reload
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# # from backend.database import init_db
# from backend.routes import jobs, reports, community, analyze, users
# import os
# from dotenv import load_dotenv

# load_dotenv()

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Startup and shutdown events"""
#     print("🚀 Starting ScamDetect API...")
#     # init_db()
#     print("✅ Database initialized")
#     yield
#     print("🛑 Shutting down...")

# app = FastAPI(
#     title="ScamDetect API",
#     description="Fake Job & Internship Scam Detection System",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # CORS configuration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, replace with specific origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Register routers
# app.include_router(users.router, prefix="/api", tags=["Users"])
# app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
# app.include_router(reports.router, prefix="/api", tags=["Reports"])
# app.include_router(community.router, prefix="/api", tags=["Community"])
# app.include_router(analyze.router, prefix="/api", tags=["Analyze"])

# @app.get("/")
# async def root():
#     return {"message": "ScamDetect API is running", "version": "1.0.0"}

# @app.get("/health")
# async def health():
#     return {"status": "healthy"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import users

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "API Running"}