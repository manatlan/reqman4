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

jar=httpx.Cookies()
# AHTTP = httpx.AsyncClient(follow_redirects=True,verify=False,cookies=jar)
# AHTTP = httpx.Client(follow_redirects=True,verify=False,cookies=jar)

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

async def call(method, url:str,body:bytes|None=None, headers:httpx.Headers = httpx.Headers(), timeout:int=60_000, proxies=None) -> httpx.Response:
    logger.debug(f"REQUEST {method} {url} with body={body} headers={headers} timeout={timeout} proxies={proxies}")

    hostfake="http://test"

    # Simule une réponse HTTP
    if url.startswith(hostfake):
        # if method == "GET" and url.startswith(f"{hostfake}/testdict"):  # DEPRECATED
        #     r= httpx.Response(
        #         status_code=200,
        #         headers={"content-type": "application/json"},
        #         json={
        #             "coco": "VAL",
        #             "liste": [1, 2, {"key": "val"}]
        #         },
        #         request=httpx.Request(method, url, headers=headers, content=body and str(body))
        #     )
        # elif method == "GET" and url.startswith(f"{hostfake}/testlist"): # DEPRECATED
        #     r= httpx.Response(
        #         status_code=200,
        #         headers={"content-type": "application/json"},
        #         json=[1, 2, {"key": "val"}]
        #         ,
        #         request=httpx.Request(method, url, headers=headers, content=body and str(body))
        #     )
        if method == "GET" and url.startswith(f"{hostfake}/test"):
            request=httpx.Request(method, url, headers=headers, content=body and str(body))
            jzon = request.url.params.get("json",None)
            r= httpx.Response(
                status_code=200,
                headers={"content-type": "application/json"},
                json=jzon and json.loads(jzon) or None,
                request=request
            )
        elif method == "POST" and url.startswith(f"{hostfake}/test"):
            r= httpx.Response(
                status_code=201,
                headers={"content-type": "application/json"},
                json=dict(result=body),
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

            # AHTTP._get_proxy_map(proxies, False)
            AHTTP = httpx.AsyncClient(follow_redirects=True,verify=False,cookies=jar)

            r= await AHTTP.request(
                method,
                url,
                data=body,
                headers=headers,
                timeout=timeout,   # sec to millisec
            )

            # info = "%s %s %s" % (r.http_version, int(r.status_code), r.reason_phrase)

        except (httpx.TimeoutException):
            r= ResponseTimeout()
        except (httpx.ConnectError):
            r= ResponseUnreachable()
        except (httpx.InvalidURL,httpx.UnsupportedProtocol,ValueError):
            r= ResponseInvalid(url)

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

