from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.auth import router as auth_router
from app.api.research import router as research_router

app = FastAPI(title="AI Research Agent API", version="0.1.0")

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