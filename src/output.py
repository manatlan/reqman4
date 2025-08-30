# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
import scenario
import logging
import json
logger = logging.getLogger(__name__)


REQUEST="""
<div class="request hide">
    <div class="click" onclick="this.parentElement.classList.toggle('hide')" title="Click to show/hide details">
        <h3>{r.request.method} {r.request.url} <span class="status">➔ {r.response.status_code}</span></h3>
        <div class="doc">{r.doc}</div>
    </div>

    <div class="detail">
<pre class="request" title="request">
{r.request.method} {r.request.url}
{rqh}

{rqc}
</pre>
➔ {r.response.http_version} {r.response.status_code} {r.response.reason_phrase} 
<pre class="response" title="response">
{rph}

{rpc}
</pre>
    </div>

    <ul class="tests">
        {tests}
    </ul>
</div>
"""

def prettify(body:bytes) -> str:
    try:
        return json.dumps(json.loads(body), indent=2, sort_keys=True)
    except:
        try:
            return body.decode()
        except:
            return str(body)

def generate_base() -> str:
    return """
<style>
body {font-family: 'Inter', sans-serif;}
h2 {color:blue}
h3 {width:100%;padding:0px;margin:0px}
div.request {margin-left:10px}
div.click {cursor:pointer;background:#F0F0F0;border-radius:4px}
div.request.hide div.detail {display:None}
div.detail {padding-left:10px}

pre {padding:4px;border:1px solid #CCC;max-height:300px;margin:2px;width:99%;display:block;overflow:auto;background:#F8F8F8;font-size:0.8em}
pre.request {}
pre.response {}
div.doc {}
span.status {float:right;color:#888}
ul.tests li.True {color:green}
ul.tests li.False {color:red}
</style>
"""

def generate_section(file:str) -> str:
    return f"<h2>{file}</h2>"

def generate_request(r:scenario.Result) -> str:
    def h(d:dict) -> str:
        ll = list(dict(d).items())
        return "\n".join( [f"{k:30s}: {v}" for k,v in ll] )
    def c(body:bytes) -> str:
        return prettify(body)
    def t(ll:list) -> str:
        return "\n".join( [f"<li class={v}>{v and 'OK' or 'KO'} : {k}</li>" for k,v in ll] )

    return REQUEST.format(
        r=r,

        rqh = h(r.request.headers),
        rqc = c(r.request.content),

        rph = h(r.response.headers),
        rpc = c(r.response.content),

        tests = t(r.tests)

    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    body=dict(var=42,val=[1,2,3])

    import httpx
    rq=httpx.Request("GET", "https://fqfdsfds/gfdsgfd?fd=15", headers={"content-type": "application/json"}, json=body)
    rp=httpx.Response(
        status_code=201,
        headers={"content-type": "application/json"},
        json=body,
    )    
    
    r = scenario.Result(rq,rp,[("status == 200",True)],doc="tet a la con")
    print(generate_request(r))

