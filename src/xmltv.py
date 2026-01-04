"""
Functions for assembling an XMLTV document from channel and programme data.

This module encapsulates the logic for cleaning text, parsing durations,
serialising channels and programmes to XML, and writing files atomically.
"""

import os
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

from lxml import etree

__all__ = [
    "clean_text",
    "remove_control_characters",
    "parse_duration",
    "build_xmltv",
    "write_atomic",
]


def remove_control_characters(s: str) -> str:
    """Remove all control characters from the given string."""
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


def clean_text(text: str) -> str:
    """Clean a piece of text for inclusion in XML.

    This function removes control characters, feature tags (e.g. [AD], [HD])
    and season/episode annotations to improve readability.

    Args:
        text: The text to clean.

    Returns:
        The cleaned text.
    """
    text = remove_control_characters(text)
    # Remove feature tags such as [S], [S,SL], [AD], [HD]
    text = re.sub(r"\[[A-Z,]+\]", "", text)
    # Remove season/episode information like "(Ep 4/10)" or "S3 Ep5"
    text = re.sub(r"\(?[SE]?\d+\s?Ep\s?\d+[\d/]*\)?", "", text)
    return text.strip()


def parse_duration(iso_duration: str) -> timedelta:
    """Parse an ISO 8601 duration string into a :class:`timedelta`.

    Years and months are not handled because they are ambiguous with respect
    to a concrete number of days.

    Args:
        iso_duration: An ISO 8601 duration string (e.g. ``PT1H30M``).

    Returns:
        A :class:`datetime.timedelta` representing the duration.
    """
    m = re.match(
        r"^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?$",
        iso_duration,
    )
    if m is None:
        raise ValueError(f"invalid ISO 8601 duration string: {iso_duration}")
    years = int(m.group(1) or 0)
    months = int(m.group(2) or 0)
    days = int(m.group(3) or 0)
    hours = int(m.group(4) or 0)
    minutes = int(m.group(5) or 0)
    seconds = float(m.group(6) or 0.0)
    # Ignore years and months due to ambiguity
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def _safe_int(value) -> int:
    """Safely convert a value to a positive integer or return None."""
    try:
        i = int(value)
        return i if i > 0 else None
    except Exception:
        return None


def build_xmltv(channels: List[Dict], programmes: List[Dict], tz) -> bytes:
    """Construct an XMLTV document from channels and programmes.

    Channels and programmes are sorted deterministically to ensure stable
    output between runs. Programmes must already be deduplicated before
    calling this function.

    Args:
        channels: List of channel dictionaries as read from ``channels.json``.
        programmes: List of programme dictionaries produced by providers.
        tz: A timezone object (e.g. from ``pytz.timezone('Europe/London')``)
            used to format timestamps.

    Returns:
        A byte string containing the pretty-printed XMLTV document.
    """
    dt_format = "%Y%m%d%H%M%S %z"
    root = etree.Element("tv")
    root.set("generator-info-name", "freeview-epg")
    root.set("generator-info-url", "https://github.com/dp247/Freeview-EPG")

    # Sort channels by their xmltv identifier for deterministic output
    for ch in sorted(channels, key=lambda c: c.get("xmltv_id")):
        channel_el = etree.SubElement(root, "channel")
        channel_el.set("id", ch.get("xmltv_id"))
        name_el = etree.SubElement(channel_el, "display-name")
        name_el.set("lang", ch.get("lang"))
        name_el.text = ch.get("name")
        if ch.get("icon_url"):
            icon_el = etree.SubElement(channel_el, "icon")
            icon_el.set("src", ch.get("icon_url"))
            icon_el.text = ""

    # Sort programmes deterministically by channel, start time, stop time and title
    for pr in sorted(
        programmes,
        key=lambda p: (
            p.get("channel", ""),
            p.get("start", 0),
            p.get("stop", 0),
            p.get("title", ""),
        ),
    ):
        programme_el = etree.SubElement(root, "programme")
        start_time = datetime.fromtimestamp(pr.get("start"), tz).strftime(dt_format)
        end_time = datetime.fromtimestamp(pr.get("stop"), tz).strftime(dt_format)
        programme_el.set("channel", pr.get("channel"))
        programme_el.set("start", start_time)
        programme_el.set("stop", end_time)

        title_el = etree.SubElement(programme_el, "title")
        title_el.set("lang", "en")
        title_el.text = pr.get("title")

        desc = pr.get("description")
        if desc:
            desc_el = etree.SubElement(programme_el, "desc")
            desc_el.set("lang", "en")
            desc_el.text = clean_text(desc)

        icon = pr.get("icon")
        if icon:
            icon_el = etree.SubElement(programme_el, "icon")
            icon_el.set("src", icon)

        if pr.get("premiere"):
            etree.SubElement(programme_el, "premiere")

        season = _safe_int(pr.get("season"))
        episode = _safe_int(pr.get("episode"))
        if season and episode:
            ep_ns = etree.SubElement(programme_el, "episode-num")
            ep_ns.set("system", "xmltv_ns")
            # xmltv_ns is zero-based
            ep_ns.text = f"{season - 1}.{episode - 1}.0"
            ep_os = etree.SubElement(programme_el, "episode-num")
            ep_os.set("system", "onscreen")
            ep_os.text = f"S{season}E{episode}"

    # Return the pretty-printed XML string as bytes
    return etree.tostring(root, pretty_print=True, encoding="utf-8")


def write_atomic(path: str, data: bytes) -> None:
    """Write data to a file atomically.

    Writes to a temporary file and then renames it into place. On POSIX
    systems the rename is atomic, ensuring readers never see a partially
    written file.

    Args:
        path: The destination file path.
        data: The data to write.
    """
    tmp_path = Path(f"{path}.tmp")
    with open(tmp_path, "wb") as f:
        f.write(data)
    os.replace(tmp_path, path)
