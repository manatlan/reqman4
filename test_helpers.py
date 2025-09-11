import respx
import httpx
import json
from contextlib import contextmanager

@contextmanager
def mock_http_test():
    hostfake = "http://test"

    def callback(request):
        if request.url.path.startswith("/test"):
            if request.method == "GET":
                jzon = request.url.params.get("json", None)
                return httpx.Response(
                    status_code=200,
                    headers={"content-type": "application/json"},
                    json=json.loads(jzon) if jzon else None,
                )
            elif request.method == "POST":
                try:
                    body = json.loads(request.content)
                except (json.JSONDecodeError, TypeError):
                    body = request.content.decode()
                return httpx.Response(
                    status_code=201,
                    headers={"content-type": "application/json"},
                    json=body,
                )
        elif request.url.path == "/headers":
            if request.method == "GET":
                return httpx.Response(
                    status_code=200,
                    headers={"content-type": "application/json"},
                    json=dict(headers=dict(request.headers)),
                )

        return httpx.Response(
            status_code=404,
            headers={"content-type": "text/plain"},
            content=b"Not Found",
        )

    with respx.mock(base_url=hostfake, assert_all_called=False) as mock:
        mock.route().mock(side_effect=callback)
        yield
