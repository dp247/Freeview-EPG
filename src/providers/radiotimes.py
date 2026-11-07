"""
RadioTimes EPG provider implementation.

Fetches programme data from the RadioTimes API. For the required number of days, 
a schedule endpoint is queried. Additional details for each episode are retrieved 
to obtain descriptions and images. Duplicate broadcasts (with the same start time) 
are skipped to avoid repeated entries.

RadioTimes represents periods where a local station simulcasts a national feed
(or otherwise has no unique listing) as ``type: "offAir"`` entries, and these
entries often omit ``start``/``end`` on the boundaries of the requested range.
Previously these were dropped entirely, leaving large holes in the guide. They
are now converted into filler programmes so the output has no gaps.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from .base import Context

FILLER_TITLE = "No Schedule Information"


def _parse_timestamp(raw: Optional[str]) -> Optional[datetime]:
    """Parse an RT ISO-8601 timestamp, returning ``None`` if absent/invalid."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _filler(xmltv_id: str, start_ts: float, end_ts: float) -> Dict[str, Any]:
    """Build a placeholder programme covering a gap in the schedule."""
    return {
        "title": FILLER_TITLE,
        "description": None,
        "start": start_ts,
        "stop": end_ts,
        "icon": None,
        "channel": xmltv_id,
    }


def fetch_programmes(channel: Dict[str, Any], ctx: Context) -> List[Dict[str, Any]]:
    """Fetch programme data for a RadioTimes channel.

    Args:
        channel: The channel definition from ``channels.json``.
        ctx: Shared context carrying a ``requests.Session`` and caches.

    Returns:
        A list of programme dictionaries for the channel.
    """
    programmes: List[Dict[str, Any]] = []
    provider_id = channel.get("provider_id")
    xmltv_id = channel.get("xmltv_id")
    session = ctx.session
    # Compute midnight UTC today and the next (ctx.days-1) days
    base = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    date_list = [base + timedelta(days=i) for i in range(ctx.days)]

    details_cache = ctx.caches.setdefault("rt_details", {})

    prev_end: Optional[float] = None
    for date in date_list:
        day_end = date + timedelta(days=1)
        from_str = date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        to_str = day_end.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        url = (
            f"https://www.radiotimes.com/api/broadcast/broadcast/channels/{provider_id}/schedule"
            f"?from={from_str}&to={to_str}"
        )
        try:
            resp = session.get(url, timeout=(5, 30))
            resp.raise_for_status()
            epg_data = resp.json()
        except Exception:
            # Skip this day on any error
            continue
        if not epg_data:
            continue
        for item in epg_data:
            # Boundary entries can omit start/end; fall back to the day's bounds.
            start_dt = _parse_timestamp(item.get("start"))
            end_dt = _parse_timestamp(item.get("end"))
            start_ts = start_dt.timestamp() if start_dt else date.timestamp()
            end_ts = end_dt.timestamp() if end_dt else day_end.timestamp()
            if end_ts <= start_ts:
                continue

            # Fill any hole left before this item (e.g. an errored day or missing slot).
            if prev_end is not None and start_ts > prev_end:
                programmes.append(_filler(xmltv_id, prev_end, start_ts))

            if item.get("type") == "offAir":
                # Off-air/simulcast slot with no unique listing: use a filler instead of a gap.
                programmes.append(_filler(xmltv_id, start_ts, end_ts))
                prev_end = end_ts
                continue

            # Fetch details for description and image
            desc = None
            icon = None
            programme_id = item.get("id")
            if programme_id:
                details_url = (
                    f"https://www.radiotimes.com/api/broadcast/broadcast/details/{programme_id}"
                )
                try:
                    details_json = details_cache.get(programme_id)
                    if details_json is None:
                        details_resp = session.get(details_url, timeout=(5, 30))
                        details_resp.raise_for_status()
                        details_json = details_resp.json()
                        details_cache[programme_id] = details_json
                    desc = details_json.get("description")
                    image = details_json.get("image")
                    if image and image.get("url"):
                        icon = image.get("url")
                except Exception:
                    pass
            title = item.get("title")

            category = None
            if item.get("genre") and len(item.get("genre")) > 0:
                category = ', '.join([g.get("name", "").capitalize() for g in item.get("genre")]).strip()
            if category is not None and item.get("type") == "film":
                category = "Film, " + category
            elif item.get("type") == "film":
                category = "Movie"

            # Skip duplicate broadcasts with the same start time as the previous real entry
            if (
                programmes
                and programmes[-1].get("title") != FILLER_TITLE
                and programmes[-1].get("start") == start_ts
            ):
                continue
            programmes.append(
                {
                    "title": title,
                    "description": desc,
                    "start": start_ts,
                    "stop": end_ts,
                    "icon": icon,
                    "channel": xmltv_id,
                    "category": category,
                }
            )
            prev_end = end_ts
    return programmes
