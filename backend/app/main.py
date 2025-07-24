from fastapi import FastAPI
from app.api.api import router as api_router

app = FastAPI(
    title="Coinfrs API",
    description="API for the Coinfrs platform.",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok"}
