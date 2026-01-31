from datetime import datetime, timedelta, timezone

import pytest

pytz = pytest.importorskip("pytz")
requests = pytest.importorskip("requests")
responses = pytest.importorskip("responses")
freeze_time = pytest.importorskip("freezegun").freeze_time

from src.providers.base import Context
from src.providers.radiotimes import fetch_programmes


@freeze_time("2024-01-02 12:00:00", tz_offset=0)
@responses.activate
def test_radiotimes_fetch_programmes_includes_details():
    session = requests.Session()
    ctx = Context(session=session, tz=pytz.UTC, days=1, caches={})
    channel = {"provider_id": "rt-1", "xmltv_id": "rt.test"}

    base = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    from_str = base.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    to_str = (base + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    responses.get(
        f"https://www.radiotimes.com/api/broadcast/broadcast/channels/rt-1/schedule"
        f"?from={from_str}&to={to_str}",
        json=[
            {
                "type": "episode",
                "id": "episode-1",
                "title": "Radio Show",
                "start": "2024-01-02T00:00:00Z",
                "end": "2024-01-02T01:00:00Z",
            }
        ],
    )

    responses.get(
        "https://www.radiotimes.com/api/broadcast/broadcast/details/episode-1",
        json={
            "description": "Radio details",
            "image": {"url": "http://img/radio.png"},
        },
    )

    programmes = fetch_programmes(channel, ctx)

    assert len(programmes) == 1
    programme = programmes[0]
    assert programme["title"] == "Radio Show"
    assert programme["description"] == "Radio details"
    assert programme["icon"] == "http://img/radio.png"
    assert programme["channel"] == "rt.test"
