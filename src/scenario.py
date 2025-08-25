import yaml,json
import asyncio
from dataclasses import dataclass
import httpx

from env import Env
import request
import pycode

import logging
logger = logging.getLogger(__name__)


@dataclass
class Result:
    request: httpx.Request
    response: httpx.Response
    tests: list[tuple[str,bool]]  # (test, result)
    file: str = ""
    doc: str = ""

class Step:
    async def execute(self,e:Env) -> list[Result]:
        pass

class StepCall(Step):
    def __init__(self, scenarios:list[Step], params:list=None):
        self.scenarios = scenarios
        self.iter = params

    async def execute(self,e:Env) -> list[Result]:
        ll=[]
        for p in self.iter or [None]:
            if p:
                # print(":: POUR",p)
                e.update(p)

            for s in self.scenarios:
                # print(f"- CALL {self.scenarios}")
                ll.extend( await s.execute(e) )
        return ll

    def __repr__(self):
        s=""
        for i in self.scenarios:
            s+= "  - "+repr(i)+"\n"
        if self.iter:
            return f"CALL MULTIPLE with {self.iter}:\n"+s
        else:
            return f"CALL:\n"+s



class StepHttp(Step):
    def __init__(self, step: dict, params: list=None):
        methods = set(step.keys()) & request.KNOWNVERBS
        assert len(methods) == 1, f"Step must contain exactly one HTTP method, found {methods}"
        method = methods.pop()
        self.method = method
        self.url = step[method]
        self.doc = step.get("doc","")
        self.headers = step.get("headers",{})
        self.body = step.get("body",None)
        self.tests = step.get("tests",[])
        assert all( isinstance(t,str) for t in self.tests ), "tests must be a list of strings"

        self.iter = params

    async def execute(self,e:Env) -> list[Result]:
        self.results=[]
        # simule l'appel

        ll=[]

        for p in self.iter or [None]:
            if p:
                # print(":: POUR",p)
                e.update(p)

            host = e.get("host",None)
            if host:
                if host == "test":
                    url = self.url
                else:
                    assert host.startswith("http"), f"host must start with http, found {host}"
                    if self.url.startswith("/"):
                        url = host + self.url
                    else:
                        if not self.url.startswith("http"):
                            url = host + "/" + self.url

            url=e.substitute(url)
            doc=e.substitute(self.doc)
            body = self.body

            if body:
                if isinstance(body, str):
                    body = e.substitute(body)
                else:
                    if isinstance(body, dict) or isinstance(body, list):
                        def substitute(o):
                            if isinstance(o, str):
                                return e.substitute(o)
                            elif isinstance(o, dict):
                                return {k:substitute(v) for k,v in o.items()}
                            elif isinstance(o, list):
                                return [substitute(v) for v in o]
                            else:
                                return o
                        body = substitute(body)
                    else:
                        body = body

            r = await request.call(self.method, url, body)
            e.setHttpResonse( r )

            # print( f"HTTP {self.method} {url} -> {r}" )

            results=[]
            for t in self.tests:
                result = e.eval(t)
                # print(" -",result and "OK" or "KO",":", t)
                results.append( (t,result) )

            ll.append( Result(r.request,r, results, doc=doc) )

        return ll
    

    def __repr__(self):
        if self.iter:
            return f"HTTP MULTIPLE {self.method} {self.url} with {self.iter}"
        else:   
            return f"HTTP {self.method} {self.url}"

class StepSet(Step):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    async def execute(self,e:Env) -> list[Result]:
        e[self.key]=e.eval(self.value)
        return []

    def __repr__(self):
        return f"SET {self.key} = {self.value}"

class Scenario(list):
    def __init__(self, file_path: str):
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        self._dico = data
        list.__init__(self,[])

        if "RUN" in self._dico:
            run = self._dico["RUN"]
            del self._dico["RUN"]
            assert isinstance(run, list), "RUN must be a list"

            pycode.declare_methods(self._dico)

            self.extend( self._feed( run ) )
        else:
            raise ValueError("No RUN section in scenario")

    @property
    def env(self):
        return self._dico

    def _feed(self, liste:list) -> list:
        ll = []
        for step in liste:
            if "params" in step:
                params=step["params"]
                if isinstance(params, dict):
                    params=[params]
                assert isinstance(params, list), "params must be a list of dict"
                del step["params"]
            else:
                params=None

            if "set" in step:
                assert params is None, "params cannot be used with set"
                assert isinstance(step["set"], dict), "SET must be a dictionary"
                assert len(step) == 1, "SET cannot be used with other keys"
                for k, v in step["set"].items():
                    ll.append( StepSet( k, str(v) ) )
            else:
                if "call" in step:
                    # assert len(step) == 1, "call cannot be used with other keys"
                    assert isinstance(step["call"], str), "CALL must be a string"
                    assert step["call"] in self.env, f"CALL references unknown scenario '{step['call']}'"
                    sub_scenar = self.env[step["call"]]
                    if isinstance(sub_scenar, dict):
                        sub_scenar = [sub_scenar]
                    scenaris = self._feed( sub_scenar )
                    self.append( StepCall( scenaris, params ) )
                else:
                    if "GET" in step or "POST" in step:
                        ll.append( StepHttp( step, params ) )
        return ll
    
    def __repr__(self):
        return super().__repr__()

async def execute(s:Scenario,e:Env) -> list[Result]:
    ll=[]
    for step in s:
        ll.extend( await step.execute(e) )
    return ll

def view(file:str) -> Scenario:
    s=Scenario(file)
    return s


async def test(file:str) -> list[Result]:
    s=Scenario(file)
    e=Env( **s.env )
    ll=await execute(s,e)
    print("\n\n------>", e)
    return ll

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # ll=test("examples/test1.yml")
    ll = asyncio.run( test("examples/simple.yml") )

    for i in ll:
        print(f"{i.request.method} {i.request.url} -> {i.response.status_code}")
        for t,r in i.tests:
            print(" -",r and "OK" or "KO",":", t)
        print()

