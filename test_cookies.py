# -*- coding: utf-8 -*-
import pytest
import respx
import httpx
from src.reqman4 import ehttp

@pytest.mark.asyncio
@respx.mock
async def test_cookie_persistence_with_respx():
    # Clear any existing cookies in the jar for a clean test
    ehttp.JAR.clear()

    # 1. Mock the endpoint that sets a cookie
    set_cookie_url = "https://my-test-site.com/set-cookie"
    respx.get(set_cookie_url).mock(
        return_value=httpx.Response(200, headers={"Set-Cookie": "name=value"})
    )

    # 2. Mock the endpoint that returns the cookies it received
    get_cookies_url = "https://my-test-site.com/get-cookies"

    def get_cookies_side_effect(request):
        """A respx side effect to simulate httpbin.org/cookies"""
        # Extract cookies from the request headers
        cookie_header = request.headers.get("cookie", "")
        cookies = {}
        if cookie_header:
            # Simple parsing for "key=value; ..." format
            for part in cookie_header.split("; "):
                if "=" in part:
                    key, value = part.split("=", 1)
                    cookies[key] = value
        return httpx.Response(200, json={"cookies": cookies})

    respx.get(get_cookies_url).mock(side_effect=get_cookies_side_effect)

    # 3. Make the first call to set the cookie
    response_set = await ehttp.call("GET", set_cookie_url)
    assert response_set.status_code == 200
    assert "name=value" in response_set.headers['set-cookie']


    # 4. Make the second call, which should send the cookie
    response_get = await ehttp.call("GET", get_cookies_url)
    assert response_get.status_code == 200

    # 5. Verify that the cookie was received by the mocked endpoint
    received_cookies = response_get.json().get("cookies", {})
    assert "name" in received_cookies
    assert received_cookies["name"] == "value"
