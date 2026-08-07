"""Shared parsing helpers for provider data."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional, Union


_EPOCH_MILLIS_THRESHOLD = 10**11


def parse_timestamp(value: Union[str, int, float, datetime]) -> int:
    """Parse a timestamp from ISO 8601 strings or epoch seconds/millis.

    Args:
        value: ISO 8601 string, epoch seconds, epoch millis, or datetime.

    Returns:
        The timestamp in epoch seconds.
    """
    if value is None:
        raise ValueError("timestamp value is required")
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    if isinstance(value, (int, float)):
        return _parse_epoch_number(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("timestamp value is empty")
        if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
            return _parse_epoch_number(float(text))
        dt = _parse_iso_datetime(text)
        return int(dt.timestamp())
    raise TypeError(f"unsupported timestamp type: {type(value)!r}")


def parse_duration_value(value: Union[str, int, float, timedelta]) -> int:
    """Parse a duration from seconds or ISO 8601 strings.

    Args:
        value: Duration in seconds or ISO 8601 duration string.

    Returns:
        Duration in seconds.
    """
    if value is None:
        raise ValueError("duration value is required")
    if isinstance(value, timedelta):
        return int(value.total_seconds())
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("duration value is empty")
        if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
            return int(float(text))
        if text.upper().startswith("P"):
            return _parse_iso_duration_seconds(text)
        raise ValueError(f"invalid duration value: {text}")
    raise TypeError(f"unsupported duration type: {type(value)!r}")


def pick_first_text(values: Iterable[Optional[str]]) -> Optional[str]:
    """Return the first non-empty string from the iterable."""
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return None


def _parse_epoch_number(value: Union[int, float]) -> int:
    """Convert epoch seconds or milliseconds to epoch seconds."""
    if abs(value) >= _EPOCH_MILLIS_THRESHOLD:
        return int(value / 1000)
    return int(value)


def _parse_iso_datetime(text: str) -> datetime:
    """Parse an ISO 8601 timestamp string into a timezone-aware datetime."""
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        dt = datetime.strptime(text, "%Y-%m-%dT%H:%M:%S%z")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_iso_duration_seconds(iso_duration: str) -> int:
    """Parse an ISO 8601 duration string into seconds."""
    match = re.match(
        r"^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?$",
        iso_duration,
    )
    if match is None:
        raise ValueError(f"invalid ISO 8601 duration string: {iso_duration}")
    days = int(match.group(3) or 0)
    hours = int(match.group(4) or 0)
    minutes = int(match.group(5) or 0)
    seconds = float(match.group(6) or 0.0)
    duration = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return int(duration.total_seconds())
