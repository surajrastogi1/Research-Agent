from fastapi import FastAPI,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from app.db.session import get_db
from app.api.auth import router as auth_router
from app.api.research import router as research_router

load_dotenv()

app = FastAPI(title="AI Research Agent API", version="0.1.0")

# Read allowed origins from env (comma-separated). Empty = allow none (dev-safe)
cors_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]

# During development, allow localhost so you can test from a local frontend
if not allowed_origins:
    allowed_origins = ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(research_router)


@app.get("/")
def get_health():
    return {"message" : "API is Running..."}

@app.get("/db-health")
def db_health(db:Session=Depends(get_db)):
    try:
        return {"message" : "Database Connected"}
    except Exception as e:
        raise HTTPException(
            status_code=500,detail=f"Database connection failed: {str(e)}"
        )