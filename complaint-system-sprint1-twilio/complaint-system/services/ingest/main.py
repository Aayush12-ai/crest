import os
import uuid
import logging
import redis.asyncio as aioredis
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database import get_db, engine, Base
from models import Complaint, AuditLog
from schemas import ComplaintRequest, ComplaintResponse, HealthResponse

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "info").upper()),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("ingest")

# ─── Redis client (module-level, shared across requests) ─────────────────────

redis_client: aioredis.Redis | None = None

# ─── App startup / shutdown ───────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client

    log.info("Starting ingest service...")

    # Connect to Redis
    redis_client = aioredis.from_url(
        os.environ["REDIS_URL"],
        decode_responses=True,
    )
    await redis_client.ping()
    log.info("Redis connected ✓")

    # Create tables if they don't exist (init.sql handles it too, this is a safety net)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables verified ✓")

    yield  # ← app runs here

    # Cleanup
    await redis_client.aclose()
    await engine.dispose()
    log.info("Ingest service shut down cleanly")


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="CMS — Ingest Service",
    description="Stage 01: Captures complaints from any channel and persists them.",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health(db: AsyncSession = Depends(get_db)):
    """Liveness check — confirms DB and Redis are reachable."""
    postgres_ok = redis_ok = False

    try:
        await db.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception as e:
        log.error("Postgres health check failed: %s", e)

    try:
        await redis_client.ping()
        redis_ok = True
    except Exception as e:
        log.error("Redis health check failed: %s", e)

    overall = "healthy" if (postgres_ok and redis_ok) else "degraded"
    return HealthResponse(
        status=overall,
        postgres="ok" if postgres_ok else "unreachable",
        redis="ok" if redis_ok else "unreachable",
    )


@app.post(
    "/complaint",
    response_model=ComplaintResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["ingest"],
    summary="Submit a new complaint",
)
async def ingest_complaint(
    body: ComplaintRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts a complaint from any channel.

    - **Idempotent**: sending the same `request_id` twice returns the original
      complaint without creating a duplicate.
    - **Async**: returns 202 Accepted immediately. Heavy processing (AI, normalise)
      will happen in downstream workers (future sprints).
    """
    # ── Step 1: Idempotency check via Redis ───────────────────────────────────
    idem_key = f"idem:{body.request_id}"
    existing_id = await redis_client.get(idem_key)

    if existing_id:
        log.info("Duplicate request_id=%s — returning existing complaint", body.request_id)
        # Fetch the existing row and return it
        from sqlalchemy import select
        result = await db.execute(
            select(Complaint).where(Complaint.request_id == body.request_id)
        )
        complaint = result.scalar_one_or_none()
        if complaint:
            return ComplaintResponse(
                complaint_id=complaint.complaint_id,
                request_id=complaint.request_id,
                status=complaint.status,
                message="Duplicate request — returning existing complaint",
                created_at=complaint.created_at,
            )

    # ── Step 2: Persist to PostgreSQL ─────────────────────────────────────────
    complaint = Complaint(
        request_id=body.request_id,
        user_id=body.user_id,
        channel=body.channel,
        message_original=body.message,
        status="received",
    )
    db.add(complaint)

    # Also write an audit log entry
    db.add(AuditLog(
        complaint_id=complaint.complaint_id,
        event_type="received",
        new_value={
            "channel": body.channel,
            "user_id": str(body.user_id),
            "status": "received",
        },
        actor_type="system",
    ))

    try:
        await db.flush()   # write + get complaint_id, but don't commit yet
    except IntegrityError:
        # Race condition: another request snuck in with same request_id
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complaint with this request_id already exists",
        )

    # ── Step 3: Store idempotency key in Redis (24h TTL) ─────────────────────
    await redis_client.setex(idem_key, 86400, str(complaint.complaint_id))

    log.info(
        "Complaint ingested | id=%s | channel=%s | user=%s",
        complaint.complaint_id, body.channel, body.user_id,
    )

    # 202 Accepted — we have it, will process async
    return ComplaintResponse(
        complaint_id=complaint.complaint_id,
        request_id=complaint.request_id,
        status=complaint.status,
        message="Complaint received. Processing will begin shortly.",
        created_at=complaint.created_at,
    )
