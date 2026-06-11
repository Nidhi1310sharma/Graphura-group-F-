# # backend/main.py
# # to run: python -m uvicorn backend.main:app --reload


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import auth, community

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(community.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "API Running"}