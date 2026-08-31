"""
Shared slowapi Limiter instance. Defined in its own module (rather than in
app/main.py) so both the app setup and individual endpoint modules can
import it without a circular import.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])
