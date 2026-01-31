from datetime import datetime, timezone

import pytest

pytz = pytest.importorskip("pytz")
requests = pytest.importorskip("requests")
responses = pytest.importorskip("responses")
freeze_time = pytest.importorskip("freezegun").freeze_time

from src.providers.base import Context
from src.providers.freeview import fetch_programmes


@freeze_time("2024-01-02 12:00:00", tz_offset=0)
@responses.activate
def test_freeview_fetch_programmes_builds_details():
    session = requests.Session()
    ctx = Context(session=session, tz=pytz.UTC, days=1, caches={})
    channel = {
        "region_id": 123,
        "provider_id": 999,
        "xmltv_id": "freeview.test",
    }

    base = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    epoch = int(base.timestamp())

    responses.get(
        "https://www.freeview.co.uk/api/tv-guide",
        json={
            "data": {
                "programs": [
                    {
                        "service_id": 999,
                        "events": [
                            {
                                "main_title": "Morning News",
                                "secondary_title": "Headlines",
                                "start_time": "2024-01-02T00:00:00+0000",
                                "duration": "PT1H",
                                "program_id": "abc",
                                "fallback_image_url": "http://img/fallback",
                            }
                        ],
                    }
                ]
            }
        },
        match=[responses.matchers.query_param_matcher({"nid": "123", "start": str(epoch)})],
    )

    responses.get(
        "https://www.freeview.co.uk/api/program",
        json={
            "data": {
                "programs": [
                    {
                        "synopsis": {"medium": "Detailed synopsis"},
                        "image_url": "http://img/detail",
                    }
                ]
            }
        },
        match=[
            responses.matchers.query_param_matcher(
                {
                    "sid": "999",
                    "nid": "123",
                    "pid": "abc",
                    "start_time": "2024-01-02T00:00:00+0000",
                    "duration": "PT1H",
                }
            )
        ],
    )

    programmes = fetch_programmes(channel, ctx)

    assert len(programmes) == 1
    programme = programmes[0]
    assert programme["title"] == "Morning News"
    assert programme["description"] == "Detailed synopsis"
    assert programme["icon"] == "http://img/detail?w=800"
    assert programme["channel"] == "freeview.test"
