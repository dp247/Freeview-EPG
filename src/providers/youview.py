"""
YouView (EE) EPG provider implementation.

Fetches programme schedules from the YouView linear metadata API using a
service locator. Episode metadata is enriched via the instance-id endpoint,
and images are derived from the instance-id when available.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from ..xmltv import parse_duration
from .base import Context


SCHEDULE_URL = "https://api.youview.tv/metadata/linear/v2/schedule/by-servicelocator"
EPISODE_URL = "https://api.youview.tv/metadata/resolution/v4/episodes/by-instance-id"
IMAGE_URL = "https://images-live.youview.tv/images/entity/{instance_id}/primary/1_512x288.jpg"


def _intervals(days: int, step_hours: int = 12) -> Iterable[str]:
    base = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    total_hours = days * 24
    for offset in range(0, total_hours, step_hours):
        start = base + timedelta(hours=offset)
        yield f"{start:%Y-%m-%dT%H}Z/PT{step_hours}H"


def _extract_entries(payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    for key in ("entries", "events"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    for key in ("schedule", "schedules"):
        value = payload.get(key)
        if isinstance(value, dict):
            return _extract_entries(value)
        if isinstance(value, list):
            entries: List[Dict[str, Any]] = []
            for item in value:
                entries.extend(_extract_entries(item))
            return entries
    return []


def _parse_timestamp(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 1e11:
            timestamp /= 1000.0
        return int(timestamp)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdigit():
            return _parse_timestamp(int(text))
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            dt = datetime.fromisoformat(text)
            return int(dt.replace(tzinfo=dt.tzinfo or timezone.utc).timestamp())
        except ValueError:
            for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
                try:
                    return int(datetime.strptime(text, fmt).timestamp())
                except ValueError:
                    continue
    return None


def _parse_duration_value(value: Any) -> Optional[timedelta]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return timedelta(seconds=float(value))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdigit():
            return timedelta(seconds=int(text))
        if text.startswith("PT"):
            try:
                return parse_duration(text)
            except ValueError:
                return None
    return None


def _pick_text(*values: Any) -> Optional[str]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_episode(payload: Any) -> Optional[Dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("episode", "entity"):
            value = payload.get(key)
            if isinstance(value, dict):
                return value
        for key in ("entries", "episodes", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        return item
        return payload
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                return item
    return None


def _extract_synopsis(data: Dict[str, Any]) -> Optional[str]:
    synopsis = data.get("synopsis")
    if isinstance(synopsis, dict):
        return _pick_text(synopsis.get("long"), synopsis.get("medium"), synopsis.get("short"))
    return _pick_text(
        synopsis,
        data.get("description"),
        data.get("shortSynopsis"),
        data.get("longSynopsis"),
    )


def _extract_instance_id(entry: Dict[str, Any]) -> Optional[str]:
    for key in ("instanceId", "instance_id", "instanceID"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    instance = entry.get("instance")
    if isinstance(instance, dict):
        value = instance.get("id") or instance.get("instanceId")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _fetch_episode_details(instance_id: str, ctx: Context) -> Optional[Dict[str, Any]]:
    cache: Dict[str, Optional[Dict[str, Any]]] = ctx.caches.setdefault(
        "youview_episode_details", {}
    )
    if instance_id in cache:
        return cache[instance_id]
    try:
        resp = ctx.session.get(
            EPISODE_URL, params={"instanceId": instance_id}, timeout=(5, 30)
        )
        resp.raise_for_status()
        details = _extract_episode(resp.json())
    except Exception:
        details = None
    cache[instance_id] = details
    return details


def fetch_programmes(channel: Dict[str, Any], ctx: Context) -> List[Dict[str, Any]]:
    """Fetch programme data for a YouView channel.

    Args:
        channel: The channel definition from ``channels.json``.
        ctx: Shared context carrying a ``requests.Session`` and caches.

    Returns:
        A list of programme dictionaries for the channel.
    """
    programmes: List[Dict[str, Any]] = []
    service_locator = channel.get("provider_id")
    xmltv_id = channel.get("xmltv_id")
    if not service_locator or not xmltv_id:
        return programmes

    seen: set[tuple[str, int]] = set()

    for interval in _intervals(ctx.days, step_hours=12):
        try:
            resp = ctx.session.get(
                SCHEDULE_URL,
                params={"serviceLocator": service_locator, "interval": interval},
                timeout=(5, 30),
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            continue

        for entry in _extract_entries(payload):
            title = _pick_text(entry.get("title"), entry.get("programmeTitle"))
            start_ts = _parse_timestamp(
                entry.get("start")
                or entry.get("startTime")
                or entry.get("startTimeUtc")
                or entry.get("startTimeUTC")
            )
            end_ts = _parse_timestamp(
                entry.get("end")
                or entry.get("endTime")
                or entry.get("endTimeUtc")
                or entry.get("endTimeUTC")
            )
            if start_ts is None:
                continue
            if end_ts is None:
                duration_td = _parse_duration_value(
                    entry.get("duration")
                    or entry.get("durationSeconds")
                    or entry.get("durationMillis")
                    or entry.get("durationMs")
                    or entry.get("durationIso")
                )
                if duration_td is None:
                    continue
                end_ts = int(start_ts + duration_td.total_seconds())

            instance_id = _extract_instance_id(entry)
            if instance_id:
                dedupe_key = (instance_id, start_ts)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

            details = _fetch_episode_details(instance_id, ctx) if instance_id else None
            description = _pick_text(
                entry.get("synopsis"),
                entry.get("description"),
                _extract_synopsis(details) if details else None,
            )
            if title is None and details:
                title = _pick_text(details.get("title"), details.get("name"))
            if title is None:
                continue

            icon = None
            if instance_id:
                icon = f"{IMAGE_URL.format(instance_id=instance_id)}?overlaygradient=0"
            elif details and isinstance(details.get("image"), dict):
                icon = details["image"].get("url")

            season = None
            episode = None
            if details:
                season = (
                    details.get("seasonNumber")
                    or details.get("seriesNumber")
                    or details.get("season")
                )
                episode = details.get("episodeNumber") or details.get("episode")

            programmes.append(
                {
                    "title": title,
                    "description": description,
                    "start": start_ts,
                    "stop": end_ts,
                    "icon": icon,
                    "channel": xmltv_id,
                    "season": season,
                    "episode": episode,
                }
            )
    return programmes
