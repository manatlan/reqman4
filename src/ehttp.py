# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
import json
import httpx
import logging
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

class ResponseError(httpx.Response):
    def __init__(self,error):
        self.error = error
        super().__init__(0,headers={},content=error.encode())
        
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.error}>"

class ResponseTimeout(ResponseError):
    def __init__(self):
        ResponseError.__init__(self,"Timeout")

class ResponseUnreachable(ResponseError):
    def __init__(self):
        ResponseError.__init__(self,"Unreachable")

class ResponseInvalid(ResponseError):
    def __init__(self,url):
        ResponseError.__init__(self,f"Invalid {url}")

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

        assert method in KNOWNVERBS, f"Unknown HTTP verb {method}"
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
            r = ResponseTimeout()
            r.request = e.request
        except httpx.ConnectError as e:
            r = ResponseUnreachable()
            r.request = e.request
        except (httpx.InvalidURL,httpx.UnsupportedProtocol,ValueError) as e:
            r = ResponseInvalid(url)
            r.request = httpx.Request(method, url, headers=headers, content=body and str(body))

    logger.debug(f"RESPONSE {r.status_code} {r.headers} {r.content}")
    return r

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import asyncio
    async def main():
        # x=await call("GET", "https://tools-httpstatus.pickup-services.com/200", proxies="http://77.232.100.132")
        x=await call("GET", "http://test/test?json=[1,2,3]")
        print(x.json())
        # print(42)
    asyncio.run(main())

