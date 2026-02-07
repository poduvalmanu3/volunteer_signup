from fastapi import FastAPI, Depends
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.deps import get_db

from app.db.check import check_db_connection
from app.api.v1.api import api_router
from app.api.auth import router as auth_router


app = FastAPI(title="Cleanup Crew")

app.include_router(auth_router)

@app.on_event("startup")
def startup_event():
    check_db_connection()

@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


app.include_router(api_router, prefix="/api/v1")
