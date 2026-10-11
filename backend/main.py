"""
MINARAM CUP — FastAPI Backend Application
Serves public read-only tournament APIs, authenticated admin operations,
and live Server-Sent Events (SSE) synchronization.
"""

import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.events import broadcaster
from app.database import Database
from app.registration_service import RegistrationService
from backend.routers import public, admin

logger = logging.getLogger("minaram_cup.api")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_ASSETS_DIR = PROJECT_ROOT / "frontend" / "public" / "assets"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set event loop for broadcaster
    loop = asyncio.get_running_loop()
    broadcaster.set_loop(loop)
    logger.info("FastAPI lifespan: Event broadcaster loop connected.")

    # Reconcile any orphan registrations on API startup
    db = Database()
    reg_svc = RegistrationService(db)
    reconciled = reg_svc.reconcile_registrations_to_teams()
    if reconciled > 0:
        logger.info(f"Reconciled {reconciled} orphan registrations on startup.")

    yield


app = FastAPI(
    title="MINARAM CUP — Elite eSports API",
    description="Official tournament API for Minaram Cup eFootball competition. Public read-only endpoints & secured admin portal.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(public.router)
app.include_router(admin.router)

FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"

# Mount static assets (use dist/assets if built, otherwise public/assets)
if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="assets")
elif STATIC_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_ASSETS_DIR)), name="assets")


# ----------------------------------------------------
# Server-Sent Events (SSE) Live Stream Endpoint
# ----------------------------------------------------
@app.get("/api/events")
async def tournament_live_events(request: Request):
    """
    Server-Sent Events (SSE) live update stream.
    Notifies connected public website clients immediately whenever tournament data
    changes in the desktop manager or admin dashboard without page reloads.
    """
    queue = broadcaster.subscribe()

    async def event_generator():
        try:
            # Initial connection ping
            yield "data: {\"status\": \"listening\"}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Wait for next event with 15s heartbeat timeout
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat comment
                    yield ": ping\n\n"
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/health")
def api_health():
    return {"status": "ok", "service": "Minaram Cup Backend API"}


# ----------------------------------------------------
# SPA Frontend Serving & Fallback
# ----------------------------------------------------
if FRONTEND_DIST_DIR.exists():
    from fastapi.responses import FileResponse
    from fastapi import HTTPException

    @app.get("/{full_path:path}")
    async def serve_spa_frontend(full_path: str):
        # Never catch /api or /assets paths
        if full_path.startswith("api") or full_path.startswith("assets"):
            raise HTTPException(status_code=404, detail="Not Found")

        target_file = FRONTEND_DIST_DIR / full_path
        if full_path and target_file.is_file():
            return FileResponse(target_file)

        index_file = FRONTEND_DIST_DIR / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="Frontend index.html not found")
