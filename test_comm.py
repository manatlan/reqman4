import src.request as comm
import pytest

@pytest.mark.asyncio
async def test_invalid_url():
    x=await comm.call("GET", "htts://invalid-url")
    assert isinstance(x, comm.ResponseInvalid)

@pytest.mark.asyncio
async def test_timeout():
    x=await comm.call("GET", "https://tools-httpstatus.pickup-services.com/200?sleep=5000",timeout=1)
    assert isinstance(x, comm.ResponseTimeout)

@pytest.mark.asyncio
async def test_error_500():
    x=await comm.call("GET", "https://tools-httpstatus.pickup-services.com/500")
    assert x.status_code == 500

@pytest.mark.asyncio
async def test_error_404():
    x=await comm.call("GET", "https://www.mlan.fr/api/totoototorotr")
    assert x.status_code == 404

