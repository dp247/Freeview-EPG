"""
Configuration utilities for loading channel information.

Channels are described in a JSON file, typically ``channels.json`` at the
repository root. The structure of the JSON is expected to be a top-level
object with a ``channels`` key containing a list of channel definitions. If
the ``channels`` key is absent, the entire file is treated as the list.
"""

import json
from typing import List, Dict


def load_channels(path: str) -> List[Dict]:
    """Load channel definitions from a JSON file.

    Args:
        path: Path to the JSON file containing channel definitions.

    Returns:
        A list of channel dictionaries. Each dictionary must at least
        contain ``src`` and ``xmltv_id`` keys.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "channels" in data:
        channels = data["channels"]
    else:
        channels = data
    if not isinstance(channels, list):
        raise ValueError(f"Invalid channel configuration format in {path}")
    return channels
