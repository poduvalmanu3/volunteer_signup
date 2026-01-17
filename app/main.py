from fastapi import FastAPI
from fastapi.responses import Response

from app.db.check import check_db_connection
from app.api.v1.api import api_router

app = FastAPI(title="Cleanup Crew")

@app.on_event("startup")
def startup_event():
    check_db_connection()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


app.include_router(api_router, prefix="/api/v1")
