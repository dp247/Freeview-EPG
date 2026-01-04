"""
HTTP utilities for the Freeview-EPG project.

Provides a helper to create a configured ``requests.Session`` with retry
behaviour. All network I/O throughout the project should use the same
session to benefit from connection pooling and consistent timeouts.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def make_session() -> requests.Session:
    """Create and return a configured ``requests.Session``.

    The returned session is configured with a retry strategy that will
    automatically retry idempotent requests on transient errors (HTTP 429 and
    5xx responses). A backoff factor controls the delay between retries.

    Returns:
        A :class:`requests.Session` instance with retry behaviour.
    """
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
