from src.reqman4 import ehttp 
import pytest
import httpx
import respx

def set_cookie_side_effect(request):
    return httpx.Response(200, text='ok', headers={'set-cookie': 'key=value; path=/'})

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

@pytest.mark.asyncio
async def test_fake():
    x=await ehttp.call("GET", "http://test/test?json=[1,2,3]")
    assert x.json() == [1,2,3]

@pytest.mark.asyncio
@respx.mock
async def test_cookie_persistence():
    # first request to set a cookie
    respx.get("http://cookie.test/1").mock(side_effect=set_cookie_side_effect)
    # second request to check if the cookie is sent
    request_with_cookie = respx.get("http://cookie.test/2").mock(return_value=httpx.Response(200, text='ok'))

    # clear previous cookies
    ehttp.JAR.clear()

    # first call to get the cookie
    await ehttp.call("GET", "http://cookie.test/1")

    # second call should contains the cookie
    await ehttp.call("GET", "http://cookie.test/2")

    assert request_with_cookie.called
    assert 'cookie' in request_with_cookie.calls.last.request.headers
    assert request_with_cookie.calls.last.request.headers['cookie'] == 'key=value'
