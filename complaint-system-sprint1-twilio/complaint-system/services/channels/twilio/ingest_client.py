"""
Posts the WhatsApp complaint to the Ingest service (Stage 01).
Keeps the Twilio channel decoupled — it doesn't write to the DB directly.
"""

import os
import uuid
import logging
import httpx

log = logging.getLogger("twilio.ingest_client")

INGEST_URL = os.environ.get("INGEST_SERVICE_URL", "http://ingest:8000")

# Shared HTTP client (connection pooling)
_http = httpx.AsyncClient(timeout=10.0)


async def submit_complaint(
    user_number: str,
    message: str,
    request_id: uuid.UUID | None = None,
) -> dict:
    """
    Forward the complaint to the Ingest service.
    Returns the response JSON (contains complaint_id).

    user_number is used as a fallback user_id placeholder until
    we have a proper user lookup service (Sprint 3).
    """
    if request_id is None:
        request_id = uuid.uuid4()

    payload = {
        "request_id": str(request_id),
        "user_id":    "00000000-0000-0000-0000-000000000001",  # test user (Sprint 3 adds lookup)
        "channel":    "whatsapp",
        "message":    message,
    }

    try:
        response = await _http.post(f"{INGEST_URL}/complaint", json=payload)
        response.raise_for_status()
        data = response.json()
        log.info(
            "Complaint logged | complaint_id=%s | from=%s",
            data.get("complaint_id"), user_number
        )
        return data
    except httpx.HTTPError as e:
        log.error("Ingest service unreachable: %s", e)
        return {}
