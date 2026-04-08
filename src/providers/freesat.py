"""
Freesat EPG provider implementation.

Fetches programme data from the Freesat TV Guide API. The API is called
separately for today and the next seven days. No additional detail API is
available, so descriptions and images are taken directly from the listing
data.
"""

from typing import List, Dict, Any

from ..utils.parsing import parse_duration_value, parse_timestamp
from .base import Context


def fetch_programmes(channel: Dict[str, Any], ctx: Context) -> List[Dict[str, Any]]:
    """Fetch programme data for a Freesat channel.

    Args:
        channel: The channel definition from ``channels.json``.
        ctx: Shared context carrying a ``requests.Session`` and caches.

    Returns:
        A list of programme dictionaries for the channel.
    """
    programmes: List[Dict[str, Any]] = []
    session = ctx.session

    # Prepare headers to mimic a regular browser request. Freesat API
    # occasionally requires these headers to return data.
    headers = {
        "authority": "www.freesat.co.uk",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Opera GX";v="106"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0",
    }

    channel_id = channel.get("provider_id")
    xmltv_id = channel.get("xmltv_id")
    postcode = channel.get("postcode")

    # Set the region based on postcode. Failures here are non-fatal.
    try:
        session.post(
            "https://www.freesat.co.uk/tv-guide/api/region",
            headers=headers,
            data=f"{postcode}",
            timeout=(5, 30),
        )
    except Exception:
        pass

    # Fetch channel info (not strictly used but mirrors the original logic)
    try:
        channel_info_url = f"https://www.freesat.co.uk/tv-guide/api?post_code={postcode.replace(' ', '%')}"
        session.get(channel_info_url, headers=headers, timeout=(5, 30))
    except Exception:
        pass

    params = {"channel": [channel_id]}
    epg_data = []
    # The API exposes endpoints for successive days starting at 0.
    # Freesat's public guide is generally 7 days, so we default to ctx.days.
    for i in range(ctx.days):
        try:
            resp = session.get(
                f"https://www.freesat.co.uk/tv-guide/api/{i}",
                params=params,
                headers=headers,
                timeout=(5, 30),
            )
            resp.raise_for_status()
            data = resp.json()
            if data and isinstance(data, list) and len(data) > 0:
                events = data[0].get("event", [])
                epg_data.extend(events)
        except Exception:
            continue
    for item in epg_data:
        title = item.get("name")
        desc = item.get("description")
        start_raw = item.get("startTime")
        duration_raw = item.get("duration", 0)
        if start_raw is None:
            continue
        try:
            start = parse_timestamp(start_raw)
            duration = parse_duration_value(duration_raw)
            end = start + duration
        except Exception:
            continue
        icon = None
        if item.get("image"):
            icon = (
                f"https://fdp-sv15-image-v1-0.gcprod1.freetime-platform.net/270x180-0{item['image']}"
            )
        programmes.append(
            {
                "title": title,
                "description": desc,
                "start": start,
                "stop": end,
                "icon": icon,
                "channel": xmltv_id,
            }
        )
    return programmes
