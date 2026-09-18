import httpx

from africa_pulse.acquisition.tomtom import TomTomTrafficClient
from africa_pulse.config import RoadSample


def test_tomtom_http_error_does_not_include_request_url(monkeypatch):
    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, *_args, **_kwargs):
            return httpx.Response(400, request=httpx.Request("GET", "https://example.test"))

    monkeypatch.setattr(httpx, "Client", lambda **_kwargs: FakeClient())
    sample = RoadSample("lagos_test", "Test", 6.4, 3.4)

    try:
        TomTomTrafficClient("secret-token").fetch_flow(sample)
    except RuntimeError as error:
        assert str(error) == "TomTom request failed with HTTP 400"
    else:
        raise AssertionError("Expected a sanitized TomTom error")
