"""
JOCKY API entry point.

This is the FastAPI application object, with all routers attached.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jocky.api.routes import router
from jocky.storage.database import init_db

app = FastAPI(title="JOCKY API")

# Allow the React dev server (Vite, port 5173) to call our API.
# In production you would restrict this to your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    """Ensure the SQLite table exists before the app starts serving requests."""
    init_db()


@app.get("/api/health")
def health_check() -> dict:
    """Simple liveness check - confirms the server is up and responding."""
    return {"status": "ok"}