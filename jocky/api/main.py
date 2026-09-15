"""
JOCKY API entry point.

This is the FastAPI application object, with all routers attached.
"""

from fastapi import FastAPI

from jocky.api.routes import router
from jocky.storage.database import init_db

app = FastAPI(title="JOCKY API")
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    """Ensure the SQLite table exists before the app starts serving requests."""
    init_db()


@app.get("/api/health")
def health_check() -> dict:
    """Simple liveness check - confirms the server is up and responding."""
    return {"status": "ok"}