# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import logging
import json,html,httpx
from urllib.parse import unquote

# reqman imports
from . import common

logger = logging.getLogger(__name__)



def prettify(body:bytes) -> str:
    if not body:
        return ""
    else:
        try:
            return json.dumps(eval(body.decode()), indent=2, sort_keys=True)
        except:
            try:
                return json.dumps(json.loads(body), indent=2, sort_keys=True)
            except:
                try:
                    return html.escape(body.decode())
                except:
                    return html.escape(str(body))

def generate_base() -> str:
    return """
<meta charset="UTF-8">
<style>
body {font-family: 'Inter', sans-serif;}
h2 {color:blue}
h3 {width:100%;padding:0px;margin:0px}
div.request {margin-left:10px}
div.click {cursor:pointer;background:#F0F0F0;border-radius:4px;padding:4px}
div.request.hide div.detail {display:None}
div.detail {padding-left:10px}
.hideresponse {display:None}
pre {padding:4px;border:1px solid #CCC;max-height:300px;margin:2px;width:99%;display:block;overflow:auto;background:#F8F8F8;font-size:0.8em;border-radius:4px}
pre.request {}
pre.response {}
div.doc {}
span.status {float:right;color:#888}
ul.tests li.True {color:green}
ul.tests li.False {color:red}
ul.tests li.None {color:#D00;font-weight:800}
div.final {position:fixed; top:0px;right:0px;background:white;padding:4px;border-radius:4px}
</style>
"""

def generate_section(file:str) -> str:
    return f"<h2>{file}</h2>"

def generate_request(r:common.Result) -> str:
    def h(d:httpx.Headers) -> str:
        ll = list(dict(d).items())
        return "\n".join( [f"<b>{k}:</b> {v}" for k,v in ll] )
    def c(body:bytes) -> str:
        r=prettify(body)
        return "\n\n"+r if r else ""
    def t(ll:list[common.TestResult]) -> str:
        items = []
        for tr in ll:
            items.append(f"""<li class={tr.ok} title="{html.escape(tr.ctx)}">{str(tr)} : {tr.text}</li>""")
        return "\n".join(items)

    if r.response.status_code<=0:
        status = "❌"  
        class_hide_response="hideresponse"
    else: 
        status = str(r.response.status_code)
        class_hide_response=""

    try:
        elapsed = r.response.elapsed
    except:
        try:
            elapsed = r.response.error  #TODO: do better here
        except:
            elapsed = "test-server"
    return f"""
<div class="request hide">
    <div class="click" onclick="this.parentElement.classList.toggle('hide')" title="Click to show/hide details">
        <h3>{r.request.method} {unquote( str(r.request.url) )} <span class="status" title="{elapsed}">{status}</span></h3>
        <div class="doc">{r.doc}</div>
    </div>

    <div class="detail">
<pre class="request" title="request">
{r.request.method} {unquote( str(r.request.url) )}
{h(r.request.headers)}{c(r.request.content)}
</pre>
<span class='{class_hide_response}'>➔ {r.response.http_version} {r.response.status_code} {r.response.reason_phrase}
<pre class="response" title="response">
{h(r.response.headers)}{c(r.response.content)}
</pre>
</span>
    </div>

    <ul class="tests">
        {t(r.tests)}
    </ul>
</div>
"""

def generate_final(switch:str|None, nb_ok:int, nb_tests:int) -> str:
    title = f"<title>{switch or ''} {nb_ok}/{nb_tests}</title>"
    return f"<div class='final'>{switch+'<br>' if switch else ''}{nb_ok}/{nb_tests}</div>" + title

if __name__ == "__main__":
    ...
    # logging.basicConfig(level=logging.DEBUG)

    # body=dict(var=42,val=[1,2,3])

    # import httpx
    # rq=httpx.Request("GET", "https://fqfdsfds/gfdsgfd?fd=15", headers={"content-type": "application/json"}, json=body)
    # rp=httpx.Response(
    #     status_code=201,
    #     headers={"content-type": "application/json"},
    #     json=body,
    # )    
    
    # r = scenario.Result(rq,rp,[("status == 200",True)],doc="tet a la con")
    # print(generate_request(r))

