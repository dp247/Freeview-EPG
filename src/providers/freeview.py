"""
Freeview EPG provider implementation.

Fetches programme data from the Freeview Play API. Programme data is
retrieved for midnight UTC today and the next seven days. Additional
programme details are fetched via a secondary API endpoint, and results
are cached to avoid redundant requests. The provider returns a list of
programme dictionaries ready for XMLTV serialisation.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple, Optional

from ..utils.parsing import parse_duration_value, parse_timestamp
from .base import Context


def fetch_programmes(channel: Dict[str, Any], ctx: Context) -> List[Dict[str, Any]]:
    """Fetch programme data for a Freeview channel.

    Args:
        channel: The channel definition from ``channels.json``.
        ctx: Shared context carrying a ``requests.Session`` and caches.

    Returns:
        A list of programme dictionaries for the channel.
    """
    programmes: List[Dict[str, Any]] = []
    region_id = channel.get("region_id")
    provider_id = channel.get("provider_id")
    xmltv_id = channel.get("xmltv_id")

    # Compute midnight UTC for today and the next (ctx.days-1) days
    base = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    epoch_times = [int((base + timedelta(days=i)).timestamp()) for i in range(ctx.days)]

    # Use caches on the context to avoid redundant requests
    data_cache: Dict[Tuple[Any, int], Any] = ctx.caches.setdefault("freeview_data", {})
    # Note: we must distinguish "missing" from "cached None" (when details fetch fails).
    details_cache: Dict[Tuple[Any, int, Any, str, str], Optional[Dict]] = ctx.caches.setdefault(
        "freeview_details", {}
    )

    _missing = object()

    for epoch in epoch_times:
        data_key = (region_id, epoch)
        if data_key not in data_cache:
            url = "https://www.freeview.co.uk/api/tv-guide"
            try:
                resp = ctx.session.get(
                    url,
                    params={"nid": f"{region_id}", "start": f"{epoch}"},
                    timeout=(5, 30),
                )
                resp.raise_for_status()
                data_cache[data_key] = resp.json()
            except Exception:
                # Skip this epoch on any error
                continue
        epg_data = data_cache[data_key].get("data", {}).get("programs", [])
        for service in epg_data:
            if service.get("service_id") != provider_id:
                continue
            for listing in service.get("events", []):
                ch_name = xmltv_id
                title = listing.get("main_title")
                desc = listing.get("secondary_title") or "No further information..."
                start_time_str = listing.get("start_time")
                duration_str = listing.get("duration")
                if not start_time_str or not duration_str:
                    continue
                try:
                    start_ts = parse_timestamp(start_time_str)
                    duration_seconds = parse_duration_value(duration_str)
                except Exception:
                    continue
                end_ts = start_ts + duration_seconds
                # Build a cache key for the detail request
                service_id = service.get("service_id")
                program_id = listing.get("program_id")
                details_key = (
                    region_id,
                    service_id,
                    program_id,
                    start_time_str,
                    duration_str,
                )
                info = details_cache.get(details_key, _missing)
                if info is _missing:
                    data_url = (
                        f"https://www.freeview.co.uk/api/program?sid={service_id}&nid={region_id}"
                        f"&pid={program_id}&start_time={start_time_str}&duration={duration_str}"
                    )
                    try:
                        info_resp = ctx.session.get(data_url, timeout=(5, 30))
                        info_resp.raise_for_status()
                        res = info_resp.json()
                        programmes_list = res.get("data", {}).get("programs", [])
                        info = programmes_list[0] if programmes_list else None
                    except Exception:
                        info = None
                    details_cache[details_key] = info
                # Determine description and icon based on detail
                icon = None
                if info:
                    synopsis = info.get("synopsis")
                    if isinstance(synopsis, dict) and synopsis:
                        medium_synopsis = synopsis.get("medium")
                        if medium_synopsis:
                            desc = medium_synopsis
                    if info.get("image_url"):
                        icon = f"{info['image_url']}?w=800"
                    elif listing.get("fallback_image_url"):
                        icon = f"{listing['fallback_image_url']}?w=800"
                else:
                    # When no detail is available, keep the basic listing description and
                    # use a fallback image if available.
                    if listing.get("fallback_image_url"):
                        icon = f"{listing['fallback_image_url']}?w=800"
                programmes.append(
                    {
                        "title": title,
                        "description": desc,
                        "start": start_ts,
                        "stop": end_ts,
                        "icon": icon,
                        "channel": ch_name,
                    }
                )
    return programmes
