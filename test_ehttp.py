from src.reqman4 import ehttp 
import pytest
import httpx

@pytest.mark.asyncio
async def test_http_500():
    x=await ehttp.call("GET", "https://tools-httpstatus.pickup-services.com/500")
    assert x.status_code==500
    assert isinstance(x, httpx.Response)

@pytest.mark.asyncio
async def test_http_404():
    x=await ehttp.call("GET", "https://tools-httpstatus.pickup-services.com/unknown")
    assert x.status_code==404
    assert isinstance(x, httpx.Response)
        
@pytest.mark.asyncio
async def test_http_ResponseUnreachable():
    x=await ehttp.call("GET", "https://unknownnnxsqcsqd.com/toto")
    assert x.status_code==0
    assert isinstance(x, ehttp.ResponseUnreachable)
    print("===>",x)

@pytest.mark.asyncio
async def test_http_ResponseInvalid():
    x=await ehttp.call("GET", "httpsunknownnnxsqcsqd.com/toto")
    assert x.status_code==0
    assert isinstance(x, ehttp.ResponseInvalid)
    print("===>",x)

@pytest.mark.asyncio
async def test_http_ResponseTimeout():
    x=await ehttp.call("GET", "https://tools-httpstatus.pickup-services.com/200?sleep=5000",timeout=100)
    assert x.status_code==0
    assert isinstance(x, ehttp.ResponseTimeout)
    print("===>",x)

from test_helpers import mock_http_test

@pytest.mark.asyncio
async def test_fake():
    with mock_http_test():
        # Test GET /test
        x = await ehttp.call("GET", "http://test/test?json=[1,2,3]")
        assert x.json() == [1, 2, 3]

        # Test GET /headers
        x = await ehttp.call("GET", "http://test/headers", headers={"X-Test": "true"})
        assert x.json()["headers"]["x-test"] == "true"

        # Test POST /test
        x = await ehttp.call("POST", "http://test/test", body={"key": "value"})
        assert x.json() == {"key": "value"}

        # Test 404
        x = await ehttp.call("GET", "http://test/notfound")
        assert x.status_code == 404

