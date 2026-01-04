"""
Sky EPG provider implementation.

Fetches programme data from the Sky API using a simple HTTP GET. A separate
request is made for each day of interest (by default, today and the next six days), 
and events are collated into a list of programme dictionaries.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from .base import Context


def fetch_programmes(channel: Dict[str, Any], ctx: Context) -> List[Dict[str, Any]]:
    """Fetch programme data for a Sky channel.

    Args:
        channel: The channel definition from ``channels.json``.
        ctx: Shared context carrying a ``requests.Session`` and caches.

    Returns:
        A list of programme dictionaries for the channel.
    """
    programmes: List[Dict[str, Any]] = []

    # Generate date strings for today and the next (ctx.days-1) days in YYYYMMDD format
    now = datetime.now()
    date_strings = [(now + timedelta(days=i)).strftime("%Y%m%d") for i in range(ctx.days)]

    provider_id = channel.get("provider_id")
    xmltv_id = channel.get("xmltv_id")

    for date in date_strings:
        url = f"https://awk.epgsky.com/hawk/linear/schedule/{date}/{provider_id}"
        try:
            resp = ctx.session.get(url, timeout=(5, 30))
            resp.raise_for_status()
            result = resp.json()
        except Exception:
            # Skip this day on any network or parsing error
            continue
        schedule = result.get("schedule")
        if not schedule:
            continue
        events = schedule[0].get("events", [])
        for item in events:
            title = item.get("t")
            desc = item.get("sy")
            start_raw = item.get("st")
            duration_raw = item.get("d")
            if start_raw is None or duration_raw is None:
                continue
            try:
                start = int(start_raw)
                end = start + int(duration_raw)
            except Exception:
                continue
            # Determine the best available icon based on identifiers
            icon = None
            if item.get("programmeuuid"):
                icon = f"https://images.metadata.sky.com/pd-image/{item['programmeuuid']}/cover"
            elif item.get("seasonuuid"):
                icon = f"https://images.metadata.sky.com/pd-image/{item['seasonuuid']}/cover"
            elif item.get("seriesuuid"):
                icon = f"https://images.metadata.sky.com/pd-image/{item['seriesuuid']}/cover"
            # Determine premiere status
            premiere = bool(item.get("new")) or (
                isinstance(title, str) and title.startswith("New:")
            )
            season = item.get("seasonnumber")
            episode = item.get("episodenumber")
            programmes.append(
                {
                    "title": title,
                    "description": desc,
                    "start": start,
                    "stop": end,
                    "icon": icon,
                    "channel": xmltv_id,
                    "premiere": premiere,
                    "season": season,
                    "episode": episode,
                }
            )
    return programmes
