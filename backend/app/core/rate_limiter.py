"""Rate limiter instance for SlowAPI. Used by auth and other public endpoints."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
