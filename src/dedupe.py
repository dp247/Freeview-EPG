"""
Dedupe utilities for EPG programmes.

This module defines a function to deduplicate programme entries. Since data
from different providers or multiple days may include the same programme
multiple times, deduplication is important before writing the final XMLTV
file. The dedupe strategy here keeps the most recently seen entry for any
given (channel, start timestamp, title) triple.
"""

from typing import List, Dict, Tuple, Set


def dedupe_programmes(programmes: List[Dict]) -> List[Dict]:
    """Deduplicate a list of programme dictionaries.

    A programme is considered duplicate if it has the same channel ID,
    start timestamp and title as another programme. The last occurrence of
    a programme in the input list is kept.

    Args:
        programmes: A list of programme dictionaries.

    Returns:
        A new list with duplicates removed, preserving order of first
        appearance of unique entries.
    """
    seen: Set[Tuple[str, float, str]] = set()
    deduped: List[Dict] = []
    # Iterate in reverse to keep the last occurrence
    for pr in reversed(programmes):
        key = (pr.get("channel"), pr.get("start"), pr.get("title"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(pr)
    # Restore original order
    deduped.reverse()
    return deduped
