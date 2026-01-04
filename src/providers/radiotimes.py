"""
RadioTimes EPG provider implementation.

Fetches programme data from the RadioTimes API. For the required number of days, 
a schedule endpoint is queried. Additional details for each episode are retrieved 
to obtain descriptions and images. Duplicate broadcasts (with the same start time) 
are skipped to avoid repeated entries.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from .base import Context


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

    prev_start: float | None = None
    for date in date_list:
        from_str = date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        to_str = (date + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
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
            if item.get("type") != "episode":
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
            # Parse start and end times as timezone-aware datetimes
            start_raw = item.get("start")
            end_raw = item.get("end")
            try:
                start_dt = datetime.strptime(start_raw, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc
                )
                end_dt = datetime.strptime(end_raw, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc
                )
            except Exception:
                continue
            start_ts = start_dt.timestamp()
            end_ts = end_dt.timestamp()
            # Skip duplicate broadcasts with the same start time
            if prev_start is not None and prev_start == start_ts:
                continue
            programmes.append(
                {
                    "title": title,
                    "description": desc,
                    "start": start_ts,
                    "stop": end_ts,
                    "icon": icon,
                    "channel": xmltv_id,
                }
            )
            prev_start = start_ts
    return programmes
