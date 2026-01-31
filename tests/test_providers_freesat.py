import pytest

pytz = pytest.importorskip("pytz")
requests = pytest.importorskip("requests")
responses = pytest.importorskip("responses")

from src.providers.base import Context
from src.providers.freesat import fetch_programmes


@responses.activate
def test_freesat_fetch_programmes_builds_output():
    session = requests.Session()
    ctx = Context(session=session, tz=pytz.UTC, days=1, caches={})
    channel = {"provider_id": "200", "xmltv_id": "freesat.test", "postcode": "AB1 2CD"}

    responses.post(
        "https://www.freesat.co.uk/tv-guide/api/region",
        status=200,
    )
    responses.get(
        "https://www.freesat.co.uk/tv-guide/api",
        status=200,
    )
    responses.get(
        "https://www.freesat.co.uk/tv-guide/api/0",
        json=[
            {
                "event": [
                    {
                        "name": "Freesat Show",
                        "description": "Freesat desc",
                        "startTime": 500,
                        "duration": 300,
                        "image": "/image.png",
                    }
                ]
            }
        ],
    )

    programmes = fetch_programmes(channel, ctx)

    assert len(programmes) == 1
    programme = programmes[0]
    assert programme["title"] == "Freesat Show"
    assert programme["description"] == "Freesat desc"
    assert programme["start"] == 500
    assert programme["stop"] == 800
    assert (
        programme["icon"]
        == "https://fdp-sv15-image-v1-0.gcprod1.freetime-platform.net/270x180-0/image.png"
    )
    assert programme["channel"] == "freesat.test"
