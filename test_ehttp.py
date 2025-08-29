import ehttp 
import pytest

@pytest.mark.asyncio
async def test_invalid_url():
    x=await ehttp.call("GET", "htts://invalid-url")
    assert isinstance(x, ehttp.ResponseInvalid)

@pytest.mark.asyncio
async def test_timeout():
    x=await ehttp.call("GET", "https://tools-httpstatus.pickup-services.com/200?sleep=5000",timeout=1000)
    assert isinstance(x, ehttp.ResponseTimeout)

@pytest.mark.asyncio
async def test_error_500():
    x=await ehttp.call("GET", "https://tools-httpstatus.pickup-services.com/500")
    assert x.status_code == 500

@pytest.mark.asyncio
async def test_error_404():
    x=await ehttp.call("GET", "https://www.mlan.fr/api/totoototorotr")
    assert x.status_code == 404

@pytest.mark.asyncio
async def test_fake():
    x=await ehttp.call("GET", "http://test/test?json=[1,2,3]")
    assert x.json() == [1,2,3]

