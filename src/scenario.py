# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
import yaml,os,time
import asyncio
from dataclasses import dataclass
import httpx
from typing import AsyncGenerator

from env import Env,R
import ehttp
import pycode
import compat

import logging
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    ok: bool
    text : str
    ctx : str


@dataclass
class Result:
    request: httpx.Request
    response: httpx.Response
    tests: list[TestResult]
    file: str = ""
    doc: str = ""



class Step:
    params: list|str|None = None
    
    async def process(self,e:Env) -> AsyncGenerator:
        ...

    def extract_params(self,e:Env) -> list:
        params=self.params
        if params is None:
            return [None]
        elif isinstance(params, str):
            params = e.substitute(params)

        assert isinstance(params, list), "params must be a list of dict"
        assert all( isinstance(p, dict) for p in params ), "params must be a list of dict"
        return params


class StepCall(Step):
    def __init__(self, scenario: "Scenario", step: dict, params:list|str|None=None):
        self.scenario = scenario
        self.params = params

        # extract step into local properties
        name = step["call"]

        assert isinstance(name, str), "CALL must be a string"
        assert name in self.scenario.env, f"CALL references unknown scenario '{name}'"
        
        sub_scenar = self.scenario.env[name]
        assert isinstance(sub_scenar, list), "CALL must reference a list of steps"

        self.steps = self.scenario._feed( sub_scenar )

    async def process(self,e:Env) -> AsyncGenerator:

        params=self.extract_params(e) 

        for param in params:
            if param:
                e.update(param)

            for step in self.steps:
                async for r in step.process(e):
                    yield r
            #TODO: perhaps remove added params from scope

    def __repr__(self):
        s=""
        for i in self.steps:
            s+= "  - "+repr(i)+"\n"
        if self.params:
            return f"CALL MULTIPLE with {self.params}:\n"+s
        else:
            return f"CALL:\n"+s



class StepHttp(Step):
    def __init__(self, scenario: "Scenario", step: dict, params: list|str|None=None):
        self.scenario = scenario
        self.params = params

        # extract step into local properties
        methods = set(step.keys()) & ehttp.KNOWNVERBS
        assert len(methods) == 1, f"Step must contain exactly one HTTP method, found {methods}"
        method = methods.pop()
        self.method = method
        self.url = step[method]
        self.doc = step.get("doc","")
        self.headers = step.get("headers",{})
        self.body = step.get("body",None)
        self.tests = compat.fix_tests( step.get("tests",[]) )
        assert all( isinstance(t,str) for t in self.tests ), "tests must be a list of strings"


    async def process(self,e:Env) -> AsyncGenerator:
        self.results=[]

        params=self.extract_params(e)

        for param in params:
            if param:
                e.update(param)

            url = e.substitute(self.url)
            host = e.get("host","")
            if host:
                assert host.startswith("http"), f"host must start with http, found {host}"
                if url.startswith("/"):
                    url = host + url
            else:
                url = self.url
                
            headers = self.scenario.env.get("headers",{})
            headers.update( self.headers )
            headers = e.substitute_in_object( headers )
            
            body = self.body

            if body:
                if isinstance(body, str):
                    body = e.substitute(body)
                else:
                    if isinstance(body, dict) or isinstance(body, list):
                        body = e.substitute_in_object(body)
                    else:
                        body = body

            start = time.time()
            response = await ehttp.call(self.method, url, body, 
                headers=httpx.Headers(headers),
                proxy=e.get("proxy",None),
                timeout=e.get("timeout",60_000) # 60 sec
            )
            diff_ms = round((time.time() - start) * 1000)  # différence en millisecondes
            e.setHttpResonse( response, diff_ms )

            results=[]
            for t in self.tests:
                ok, dico = e.eval(t, with_context=True)
                context=""
                for k,v in dico.items():
                    if k=="R":      #TODO: make better
                        if "R.time" in t:
                            r:R=e["R"]
                            k,v="R.time",r.time
                        if "R.status" in t:
                            r:R=e["R"]
                            k,v="R.status",r.status
                        if "R.headers" in t:
                            r:R=e["R"]
                            k,v="R.headers",r.headers
                        if "R.content" in t:
                            r:R=e["R"]
                            k,v="R.content",r.content
                        if "R.text" in t:
                            r:R=e["R"]
                            k,v="R.text",r.text
                        if "R.json" in t:
                            r:R=e["R"]
                            k,v="R.json",r.json
                        
                    context+= f"{k}: {v}\n"
                results.append( TestResult(ok,t,context) )

            doc=e.substitute(self.doc)
            yield Result(response.request,response, results, doc=doc)

            #TODO: perhaps remove added params from scope

    

    def __repr__(self):
        if self.params:
            return f"HTTP MULTIPLE {self.method} {self.url} with {self.params}"
        else:   
            return f"HTTP {self.method} {self.url}"

class StepSet(Step):
    def __init__(self, scenario: "Scenario", step:dict):
        self.scenario = scenario

        assert len(step) == 1, "SET cannot be used with other keys"
        dico = step["set"]
        assert isinstance(dico, dict), "SET must be a dictionary"
        self.dico = dico

    async def process(self,e:Env) -> AsyncGenerator:
        e.update( self.dico )
        e.update( e.substitute_in_object(self.dico) )
        yield None

    def __repr__(self):
        return f"SET {self.dico}"

class ScenarException(Exception): pass

class Scenario(list):
    def __init__(self, file_path: str):
        if not os.path.isfile(file_path):
            raise ScenarException(f"[{file_path}] [File not found]")
        self.file_path = file_path

        try:
            with open(self.file_path, 'r') as fid:
                self._dico = yaml.safe_load(fid)
        except yaml.YAMLError as ex:
            raise ScenarException(f"[{self.file_path}] [Bad syntax] [{ex}]")
        list.__init__(self,[])

        if isinstance(self._dico, dict):
            if "RUN" in self._dico:
                run = self._dico["RUN"]
                del self._dico["RUN"]
                if not isinstance(run, list):
                    raise ScenarException(f"[{self.file_path}] [Bad syntax] [RUN must be a list]")

                pycode.declare_methods(self._dico)

                self.extend( self._feed( run ) )
            else:
                raise ScenarException("No RUN section in scenario")
        elif isinstance(self._dico, list):
            run = self._dico
            self._dico={}
            self.extend( self._feed( run ) )

        else:
            raise ScenarException(f"[{self.file_path}] [Bad syntax] [scenario must be a dict or a list]")

    @property
    def env(self) -> dict:
        return self._dico

    def _feed(self, liste:list) -> list[Step]:
        try:
            ll = []
            for step in liste:
                assert isinstance(step, dict), f"Bad step {step}"
                
                if "params" in step:
                    params=step["params"]
                    del step["params"]
                else:
                    params=None

                if "set" in step:
                    assert params is None, "params cannot be used with set"
                    ll.append( StepSet( self, step ) )
                else:
                    if "call" in step:
                        self.append( StepCall( self, step, params ) )
                    else:
                        if set(step.keys()) & ehttp.KNOWNVERBS:
                            ll.append( StepHttp( self, step, params ) )
                        else:
                            raise ScenarException(f"Bad step {step}")
            return ll
        except AssertionError as ex:
            raise ScenarException(f"[{self.file_path}] [Bad step {step}] [{ex}]")
    
    def __repr__(self):
        return super().__repr__()
    
    async def execute(self, e:Env) -> AsyncGenerator:
        for step in self:
            try:
                async for i in step.process(e):
                    yield i
            except Exception as ex:
                raise ScenarException(f"[{self.file_path}] [Error Step {step}] [{ex}]")

class Test:
    def __init__(self, file:str, conf:dict|None=None):
        self.scenario = Scenario(file)
        conf = conf or {}
        conf.update( self.scenario.env )
        self.env = Env( **conf )

    def apply_switch(self, name:str):
        assert name in dict(self.env.switchs), f"Unknown switch '{name}'"
        self.env.update( self.env.switchs[name] )

    async def run(self,switch:str|None=None) -> AsyncGenerator:
        if switch:
            self.apply_switch(switch)
        async for r in self.scenario.execute(self.env):
            yield r
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    async def run_a_test(f:str):
        t=Test(f)
        async for i in t.run():
            if i:
                print(f"{i.request.method} {i.request.url} -> {i.response.status_code}")
                for tr in i.tests:
                    print(" -",tr.ok and "OK" or "KO",":", tr.text)
                print()


    # asyncio.run( run_a_test("examples/ok/simple.yml") )
    asyncio.run( run_a_test("examples/ok/test1.yml") )
