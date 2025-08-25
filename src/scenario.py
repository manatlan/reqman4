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
    async def process(self,e:Env):
        pass

class StepCall(Step):
    def __init__(self, scenarios:list[Step], params:list=None):
        self.scenarios = scenarios
        self.iter = params

    async def process(self,e:Env):

        for p in self.iter or [None]:
            if p:
                # print(":: POUR",p)
                e.update(p)

            for s in self.scenarios:
                # print(f"- CALL {self.scenarios}")
                async for r in s.process(e):
                    yield r
        

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

    async def process(self,e:Env):
        self.results=[]
        # simule l'appel

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
            else:
                url = self.url

            url=e.substitute(url)
            doc=e.substitute(self.doc)
            body = self.body

            if body:
                if isinstance(body, str):
                    body = e.substitute(body)
                else:
                    if isinstance(body, dict) or isinstance(body, list):
                        body = e.substitute_in_object(body)
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

            yield Result(r.request,r, results, doc=doc)

    

    def __repr__(self):
        if self.iter:
            return f"HTTP MULTIPLE {self.method} {self.url} with {self.iter}"
        else:   
            return f"HTTP {self.method} {self.url}"

class StepSet(Step):
    def __init__(self, dico:dict):
        self.dico = dico

    async def process(self,e:Env):
        d=e.substitute_in_object(self.dico)
        assert isinstance(d, dict), "SET must be a dictionary"
        e.update(d)
        yield None

    def __repr__(self):
        return f"SET {self.dico}"

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
                ll.append( StepSet( step["set"] ) )
            else:
                if "call" in step:
                    # assert len(step) == 1, "call cannot be used with other keys"
                    assert isinstance(step["call"], str), "CALL must be a string"
                    assert step["call"] in self.env, f"CALL references unknown scenario '{step['call']}'"
                    sub_scenar = self.env[step["call"]]
                    assert isinstance(sub_scenar, list), "CALL must reference a list of steps"
                    scenaris = self._feed( sub_scenar )
                    self.append( StepCall( scenaris, params ) )
                else:
                    if "GET" in step or "POST" in step:
                        ll.append( StepHttp( step, params ) )
        return ll
    
    def __repr__(self):
        return super().__repr__()

async def execute(s:Scenario,e:Env) :
    for step in s:
        async for i in step.process(e):
            yield i



async def test(file:str):
    s=Scenario(file)
    e=Env( **s.env )
    async for r in execute(s,e):
        yield r
    print("======ENV FINAL==========>",e)
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # ll=test("examples/test1.yml")

    async def xxx(f:str):
        async for i in test(f):
            if i:
                print(f"{i.request.method} {i.request.url} -> {i.response.status_code}")
                for t,r in i.tests:
                    print(" -",r and "OK" or "KO",":", t)
                print()


    asyncio.run( xxx("examples/simple.yml") )

    # for i in ll:

