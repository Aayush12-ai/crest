"""
Claude-powered reply generator.
Replaces Gemini — same interface your original expected.
"""

import os
import logging
import anthropic

from memory import get_history, add_message

log = logging.getLogger("twilio.claude")

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are a helpful customer support assistant for a financial services company.
You receive complaints and queries via WhatsApp.

Your job:
1. Acknowledge the user's issue warmly and professionally
2. Confirm their complaint has been logged and will be reviewed
3. If they give details (payment failure, account issue, etc.) summarise them back
4. Give a realistic resolution timeline (24–48 hours for most issues)
5. Keep replies concise — this is WhatsApp, not email

Never make up account details, transaction statuses, or refund promises.
If you don't know something, say "our team will look into this for you."
"""


def build_messages(user_number: str, user_msg: str) -> list[dict]:
    """Convert our memory format to Anthropic messages format."""
    history = get_history(user_number)
    messages = []

    for entry in history:
        role = "user" if entry["role"] == "user" else "assistant"
        messages.append({"role": role, "content": entry["text"]})

    # Add the new message
    messages.append({"role": "user", "content": user_msg})
    return messages


def generate_reply(user_number: str, user_msg: str) -> str:
    """
    Send conversation history + new message to Claude.
    Saves the reply into memory before returning.
    """
    add_message(user_number, "user", user_msg)

    messages = build_messages(user_number, user_msg)

    try:
        response = _client.messages.create(
            model="claude-haiku-4-5-20251001",   # fast + cheap for WhatsApp replies
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        reply = response.content[0].text
        add_message(user_number, "assistant", reply)
        log.info("Claude replied to %s", user_number)
        return reply

    except anthropic.APIError as e:
        log.error("Claude API error: %s", e)
        return "⚠️ Our assistant is temporarily unavailable. Your complaint has been logged and a team member will follow up."
