"""
Rate limiting and duplicate-message protection.
Same logic as your original — just cleaned up and testable in isolation.
"""

import time

_last_message:   dict[str, str]   = {}
_last_call_time: dict[str, float] = {}

RATE_LIMIT_SECONDS = 6


class Duplicate(Exception):
    """Raised when the same message arrives again from the same user."""


class RateLimited(Exception):
    """Raised when the user is sending too fast."""


def check(user_number: str, user_msg: str) -> None:
    """
    Call before processing a message.
    Raises Duplicate or RateLimited so the caller decides what to do.
    """
    now = time.time()

    if _last_message.get(user_number) == user_msg:
        raise Duplicate(f"Duplicate message from {user_number}")

    if now - _last_call_time.get(user_number, 0) < RATE_LIMIT_SECONDS:
        raise RateLimited(f"{user_number} is sending too fast")

    # All good — record this call
    _last_message[user_number] = user_msg
    _last_call_time[user_number] = now
