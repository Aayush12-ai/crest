"""
In-memory conversation store.

In production (Sprint 6+) this moves to Redis so memory
survives container restarts and scales across multiple pods.
For now it lives here as a plain dict.
"""

from collections import defaultdict
from typing import TypedDict

MAX_HISTORY = 10  # messages to keep per user (user + bot combined)


class Message(TypedDict):
    role: str   # "user" | "assistant"
    text: str


# keyed by WhatsApp number e.g. "whatsapp:+919876543210"
_store: dict[str, list[Message]] = defaultdict(list)


def add_message(user_number: str, role: str, text: str) -> None:
    _store[user_number].append({"role": role, "text": text})
    # trim to window
    if len(_store[user_number]) > MAX_HISTORY:
        _store[user_number] = _store[user_number][-MAX_HISTORY:]


def get_history(user_number: str) -> list[Message]:
    return list(_store[user_number])


def clear(user_number: str) -> None:
    _store[user_number] = []
