# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import json
import httpx
import logging

# reqman imports
from .common import assert_syntax

logger = logging.getLogger(__name__)

KNOWNVERBS = set([
    "GET",
    "POST",
    "DELETE",
    "PUT",
    "HEAD",
    "OPTIONS",
    "TRACE",
    "PATCH",
    "CONNECT",
])

JAR=httpx.Cookies()


class MyHeaders(httpx.Headers):
    def __getattr__(self, key):
        fix=lambda x: x and x.lower().strip().replace("-","_") or None
        for k,v in super().items():
            if fix(k)==fix(key):
                return v
        return super().__getitem__(key)    

class _ResponseError_(httpx.Response):
    def __init__(self,error):
        self.error = error
        super().__init__(0,headers={})
        # super().__init__(0,headers={},content=error)
        
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.error}>"

class ResponseTimeout(_ResponseError_):
    def __init__(self,err):
        _ResponseError_.__init__(self,err)

class ResponseUnreachable(_ResponseError_):
    def __init__(self):
        _ResponseError_.__init__(self,"Unreachable")

class ResponseInvalid(_ResponseError_):
    def __init__(self):
        _ResponseError_.__init__(self,f"Invalid url")

async def call(method, url:str,body:bytes|None=None, headers:httpx.Headers = httpx.Headers(), timeout:int=60_000, proxy:str|None=None) -> httpx.Response:
    logger.debug(f"REQUEST {method} {url} with body={body} headers={headers} timeout={timeout} proxy={proxy}")

    # if proxy:
    #     transport = httpx.HTTPTransport(proxy=proxy)
    #     proxy_mounts = {"http://": transport, "https://": transport}
    # else:
    #     proxy_mounts = None

    hostfake="http://test"

    # Simule une réponse HTTP
    if url.startswith(hostfake):
        if method == "GET" and url.startswith(f"{hostfake}/test"):
            request=httpx.Request(method, url, headers=headers, content=body and str(body))
            jzon = request.url.params.get("json",None)
            r= httpx.Response(
                status_code=200,
                headers={"content-type": "application/json"},
                json=json.loads(jzon) if jzon else None,
                request=request
            )
        elif method == "GET" and url.startswith(f"{hostfake}/headers"):
            request=httpx.Request(method, url, headers=headers, content=body and str(body))
            r= httpx.Response(
                status_code=200,
                headers={"content-type": "application/json"},
                json=dict(headers=dict(request.headers)),   # destructive !
                request=request
            )
        elif method == "POST" and url.startswith(f"{hostfake}/test"):
            r= httpx.Response(
                status_code=201,
                headers={"content-type": "application/json"},
                json=body,
                request=httpx.Request(method, url, headers=headers, content=body and str(body))
            )
        else:
            r= httpx.Response(
                status_code=404,
                headers={"content-type": "text/plain"},
                content=b"Not Found",
                request=httpx.Request(method, url, headers=headers, content=body and str(body))
            )
    else:

        assert_syntax( method in KNOWNVERBS, f"Unknown HTTP verb {method}")
        try:
            if proxy:
                logger.debug("Use proxy:",proxy)
                
            if isinstance(body, dict) or isinstance(body, list):
                async with httpx.AsyncClient(follow_redirects=True,verify=False,cookies=JAR,proxy=proxy) as client:
                    r = await client.request(
                        method,
                        url,
                        json=body,
                        headers=headers,
                        timeout=timeout/1000,   # seconds!
                    )
            else:
                async with httpx.AsyncClient(follow_redirects=True,verify=False,cookies=JAR,proxy=proxy) as client:
                    r = await client.request(
                        method,
                        url,
                        data=body,
                        headers=headers,
                        timeout=timeout/1000,   # seconds!
                    )

        except httpx.TimeoutException as e:
            r = ResponseTimeout(f"Timeout (> {timeout}ms)")
            r.request = e.request
        except httpx.ConnectError as e:
            r = ResponseUnreachable()
            r.request = e.request
        except (httpx.InvalidURL,httpx.UnsupportedProtocol,ValueError) as e:
            r = ResponseInvalid()
            r.request = httpx.Request(method, url, headers=headers, content=body and str(body))

    logger.debug(f"RESPONSE {r.status_code} {r.headers} {r.content}")
    return r

if __name__ == "__main__":
    ...
    # logging.basicConfig(level=logging.DEBUG)
    # import asyncio
    # async def main():
    #     x=await call("GET", "https://tools-httpstatus.pickup-services.com/500")
    #     assert x.status_code==500
    # asyncio.run(main())

