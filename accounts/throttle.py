"""
Login throttle — 5 attempts per 5 minutes per IP+email combo.
Uses django cache (Redis) directly so it works without django-ratelimit's
decorator pattern (we need it inside a DRF view, not a function view).
"""
import hashlib
import time
from typing import Optional, Tuple

from django.core.cache import cache


THROTTLE_WINDOW = 300  # 5 minutes in seconds
THROTTLE_LIMIT = 5
LOCKOUT_DURATION = 900  # 15 minutes


def _throttle_key(ip: str, email: str) -> str:
    raw = f'login_throttle:{ip}:{email.lower()}'
    return hashlib.sha256(raw.encode()).hexdigest()


def check_login_throttle(ip: str, email: str) -> Tuple[bool, Optional[int]]:
    """
    Returns (allowed: bool, retry_after: int | None).
    If not allowed, retry_after is seconds until the window resets.
    """
    key = _throttle_key(ip, email)
    lockout_key = f'{key}:locked'

    # Check lockout first
    locked_until = cache.get(lockout_key)
    if locked_until:
        remaining = int(locked_until - time.time())
        if remaining > 0:
            return False, remaining
        cache.delete(lockout_key)

    attempts = cache.get(key, [])
    now = time.time()
    # Prune old attempts outside the window
    attempts = [t for t in attempts if now - t < THROTTLE_WINDOW]

    if len(attempts) >= THROTTLE_LIMIT:
        # Lock out for 15 minutes
        cache.set(lockout_key, now + LOCKOUT_DURATION, LOCKOUT_DURATION)
        return False, LOCKOUT_DURATION

    return True, None


def record_login_attempt(ip: str, email: str):
    """Record a failed login attempt."""
    key = _throttle_key(ip, email)
    now = time.time()
    attempts = cache.get(key, [])
    attempts = [t for t in attempts if now - t < THROTTLE_WINDOW]
    attempts.append(now)
    cache.set(key, attempts, THROTTLE_WINDOW)


def clear_login_throttle(ip: str, email: str):
    """Clear throttle on successful login."""
    key = _throttle_key(ip, email)
    cache.delete(key)
    cache.delete(f'{key}:locked')
