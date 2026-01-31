import pytest

pytz = pytest.importorskip("pytz")
requests = pytest.importorskip("requests")
responses = pytest.importorskip("responses")
freeze_time = pytest.importorskip("freezegun").freeze_time

from src.providers.base import Context
from src.providers.sky import fetch_programmes


@freeze_time("2024-01-02 12:00:00")
@responses.activate
def test_sky_fetch_programmes_parses_events():
    session = requests.Session()
    ctx = Context(session=session, tz=pytz.UTC, days=1, caches={})
    channel = {"provider_id": "1001", "xmltv_id": "sky.test"}

    responses.get(
        "https://awk.epgsky.com/hawk/linear/schedule/20240102/1001",
        json={
            "schedule": [
                {
                    "events": [
                        {
                            "t": "Test Show",
                            "sy": "Synopsis",
                            "st": 100,
                            "d": 60,
                            "programmeuuid": "abc",
                            "new": True,
                            "seasonnumber": 2,
                            "episodenumber": 5,
                        }
                    ]
                }
            ]
        },
    )

    programmes = fetch_programmes(channel, ctx)

    assert len(programmes) == 1
    programme = programmes[0]
    assert programme["title"] == "Test Show"
    assert programme["description"] == "Synopsis"
    assert programme["start"] == 100
    assert programme["stop"] == 160
    assert programme["icon"] == "https://images.metadata.sky.com/pd-image/abc/cover"
    assert programme["premiere"] is True
    assert programme["season"] == 2
    assert programme["episode"] == 5
    assert programme["channel"] == "sky.test"
