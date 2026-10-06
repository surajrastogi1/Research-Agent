from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

app = FastAPI()

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