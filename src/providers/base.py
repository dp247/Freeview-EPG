"""
Base definitions for provider modules.

The :class:`Context` class encapsulates shared state used by all provider
implementations, including a pre-configured HTTP session, a timezone
definition, and arbitrary caches for expensive lookups.
"""

from dataclasses import dataclass, field
from typing import Any, Dict

import pytz
import requests


@dataclass
class Context:
    """Shared state passed to all provider fetch functions.

    Attributes:
        session: A pre-configured :class:`requests.Session` for network calls.
        tz: A timezone object used for output formatting (e.g. Europe/London).
        caches: A dictionary of caches keyed by provider-specific names. Each
            cache should itself be a mutable object (e.g. a dict) so that
            providers can store and retrieve intermediate results across
            multiple calls.
    """
    session: requests.Session
    tz: pytz.BaseTzInfo
    # Default horizon in days. GitHub Actions uses the default to build a
    # 7-day guide without needing parameters.
    days: int = 7
    caches: Dict[str, Any] = field(default_factory=dict)
