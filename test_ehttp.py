import ehttp 
import pytest

@pytest.mark.asyncio
def test_http_500():
    x=await ehttp.call("GET", "https://tools-httpstatus.pickup-services.com/500")
    assert x.status_code==500
    assert isinstance(x, httpx.Response)

@pytest.mark.asyncio
def test_http_404():
    x=await ehttp.call("GET", "https://tools-httpstatus.pickup-services.com/unknown")
    assert x.status_code==404
    assert isinstance(x, httpx.Response)
        
@pytest.mark.asyncio
def test_http_ResponseUnreachable():
    x=await ehttp.call("GET", "https://unknownnnxsqcsqd.com/toto")
    assert x.status_code==0
    assert isinstance(x, ResponseUnreachable)
    print("===>",x)

@pytest.mark.asyncio
def test_http_ResponseInvalid():
    x=await ehttp.call("GET", "httpsunknownnnxsqcsqd.com/toto")
    assert x.status_code==0
    assert isinstance(x, ResponseInvalid)
    print("===>",x)

@pytest.mark.asyncio
def test_http_ResponseTimeout():
    x=await ehttp.call("GET", "https://tools-httpstatus.pickup-services.com/200?sleep=5000",timeout=100)
    assert x.status_code==0
    assert isinstance(x, ResponseTimeout)
    print("===>",x)

@pytest.mark.asyncio
async def test_fake():
    x=await ehttp.call("GET", "http://test/test?json=[1,2,3]")
    assert x.json() == [1,2,3]

