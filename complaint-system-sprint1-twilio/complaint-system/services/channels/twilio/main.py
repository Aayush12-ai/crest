"""
Twilio WhatsApp Channel — Stage 00/01 entry point.

Flow:
  WhatsApp message → Twilio → POST /webhook (here)
      → rate limit check
      → log complaint to Ingest service (DB row created)
      → Claude generates a reply
      → Twilio sends reply back to user
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.rest import Client as TwilioClient

import rate_limit
import ingest_client
from claude_reply import generate_reply

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("twilio.channel")

# ─── Twilio client ────────────────────────────────────────────────────────────

twilio = TwilioClient(
    os.environ["TWILIO_SID"],
    os.environ["TWILIO_AUTH_TOKEN"],
)
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER", "whatsapp:+14155238886")


def send_whatsapp(to: str, body: str) -> None:
    """Send a WhatsApp message back to the user via Twilio."""
    try:
        twilio.messages.create(from_=TWILIO_NUMBER, to=to, body=body)
        log.info("Reply sent to %s", to)
    except Exception as e:
        log.error("Twilio send failed for %s: %s", to, e)


# ─── App ──────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Twilio channel service starting...")
    yield
    await ingest_client._http.aclose()
    log.info("Twilio channel service shut down")


app = FastAPI(
    title="CMS — Twilio WhatsApp Channel",
    description="Receives WhatsApp messages, logs them as complaints, replies via Claude.",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": "twilio-channel"}


@app.post("/webhook", tags=["channel"])
async def whatsapp_webhook(request: Request):
    """
    Twilio posts here when a WhatsApp message arrives.
    Must return 200 quickly — Twilio retries on timeout.
    """
    form = await request.form()
    user_msg: str = form.get("Body", "").strip()
    user_number: str = form.get("From", "")

    log.info("Incoming | from=%s | msg=%r", user_number, user_msg[:80])

    # ── Guard: ignore empty messages ──────────────────────────────────────────
    if not user_msg:
        return PlainTextResponse("OK")

    # ── Rate limit + duplicate check ──────────────────────────────────────────
    try:
        rate_limit.check(user_number, user_msg)
    except rate_limit.Duplicate:
        log.info("Duplicate message ignored from %s", user_number)
        return PlainTextResponse("OK")
    except rate_limit.RateLimited:
        send_whatsapp(user_number, "Easy there 😄 give me a few seconds...")
        return PlainTextResponse("OK")

    # ── Log complaint to Ingest service ───────────────────────────────────────
    # Fire-and-await: we need the complaint_id before replying
    complaint_data = await ingest_client.submit_complaint(
        user_number=user_number,
        message=user_msg,
    )
    complaint_id = complaint_data.get("complaint_id", "unknown")

    # ── Generate Claude reply ─────────────────────────────────────────────────
    reply = generate_reply(user_number, user_msg)

    # Append complaint reference so user knows it's tracked
    if complaint_id != "unknown":
        reply += f"\n\n📋 Reference: #{str(complaint_id)[:8].upper()}"

    # ── Send reply via Twilio ─────────────────────────────────────────────────
    send_whatsapp(user_number, reply)

    return PlainTextResponse("OK")
