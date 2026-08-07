"""
Entry point for building the XMLTV file.

This script loads the channel configuration, dispatches programme fetching to the
provider-specific modules, deduplicates the programmes, and writes the output
to `epg.xml` using an atomic file write. The goal is to keep this file thin
and focused on orchestration rather than scraping logic.

The providers themselves live in `src/providers/`, and each exposes a
`fetch_programmes(channel: dict, ctx: Context) -> list[dict]` function. The
`Context` object provides shared state, such as a `requests.Session` with
retries and a timezone.

Usage:
    python main.py

You can adjust logging verbosity by setting the `LOGLEVEL` environment
variable (e.g. ``LOGLEVEL=DEBUG python main.py``).
"""

import logging
import os

import pytz

from src.config import load_channels
from src.dedupe import dedupe_programmes
from src.http import make_session
from src.xmltv import build_xmltv, write_atomic
from src.providers import sky, freeview, freesat, radiotimes, youview
from src.providers.base import Context


def main() -> None:
    """Main orchestration function."""
    # Load channel configuration from the default file. You can change this
    # argument to point to a different JSON file if desired.
    channels = load_channels("channels.json")

    # Set up a shared HTTP session with retry behaviour. All network
    # interactions should go through this session so that timeouts and
    # retries are handled consistently.
    session = make_session()

    # Create a context object that holds shared state. The timezone is set
    # explicitly so that timestamps are converted to the correct offset when
    # writing the XMLTV. Caches live on the context to avoid recomputing
    # expensive lookups (e.g. Freeview programme details).
    # Build a 7-day guide by default.
    ctx = Context(session=session, tz=pytz.timezone("Europe/London"), days=7, caches={})

    programmes = []

    # Iterate over each channel and dispatch to the appropriate provider
    # implementation. Unknown sources are skipped with a warning.
    for channel in channels:
        print("Fetching programmes for", channel.get("name"))
        src = channel.get("src")
        if src == "sky":
            fetcher = sky.fetch_programmes
        elif src == "freeview":
            fetcher = freeview.fetch_programmes
        elif src == "freesat":
            fetcher = freesat.fetch_programmes
        elif src == "rt":
            fetcher = radiotimes.fetch_programmes
        elif src == "yv":
            fetcher = youview.fetch_programmes
        else:
            logging.warning(
                "Unknown source '%s' for channel %s; skipping.",
                src,
                channel.get("name"),
            )
            continue

        try:
            ch_programmes = fetcher(channel, ctx)
            programmes.extend(ch_programmes)
        except Exception as exc:
            # Log and continue on provider-specific exceptions so that one
            # misbehaving source does not take down the whole build.
            logging.error(
                "Error fetching programmes for %s: %s", channel.get("name"), exc
            )
            continue

    # Deduplicate programmes across days and providers. We remove duplicates
    # based on the trio of (channel, start timestamp, title) and keep the
    # most recently fetched entry. This prevents multiple identical entries
    # appearing if, for example, the same programme is returned for several
    # days in a row.
    programmes = dedupe_programmes(programmes)

    # Build the XMLTV document. Sorting of channels and programmes is
    # performed within build_xmltv for deterministic output.
    xml_bytes = build_xmltv(channels, programmes, tz=ctx.tz)

    # Write to epg.xml atomically. This ensures that consumers never read
    # partially written files.
    write_atomic("epg.xml", xml_bytes)


if __name__ == "__main__":
    # Configure basic logging. The log level can be overridden using the
    # environment variable LOGLEVEL.
    loglevel = os.environ.get("LOGLEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, loglevel, logging.INFO))
    main()
