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
    ok: bool        # bool with 3 states : see __repr__
    text : str
    ctx : str

    def __repr__(self):
        return {True:"OK",False:"KO",None:"BUG"}[self.ok]


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
                e.scope_update(param)

            for step in self.steps:
                async for r in step.process(e):
                    yield r
                    
            e.scope_revert()

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
        assert isinstance(self.tests,list), "tests must be a list of strings"
        assert all( isinstance(t,str) for t in self.tests ), "tests must be a list of strings"


    async def process(self,e:Env) -> AsyncGenerator:
        self.results=[]

        params=self.extract_params(e)

        for param in params:
            if param:
                e.scope_update(param)

            url = e.substitute(self.url)
            root = e.get("root","")
            if root:
                if url.startswith("/"):
                    url = root + url
            assert url.startswith("http"), f"url must start with http, found {url}"
                
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
                try:
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
                except Exception as ex:
                    logger.error("Can't eval test [{t}] : {ex}")
                    results.append( TestResult(None,t,f"ERROR: {ex}") )


            doc=e.substitute(self.doc)
            yield Result(response.request,response, results, doc=doc)

            e.scope_revert()

    

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
    def __init__(self, file_path: str, env:Env):
        self.env = env
        if not os.path.isfile(file_path):
            raise ScenarException(f"[{file_path}] [File not found]")
        self.file_path = file_path

        try:
            with open(self.file_path, 'r') as fid:
                yml = yaml.safe_load(fid)
        except yaml.YAMLError as ex:
            raise ScenarException(f"[{self.file_path}] [Bad syntax] [{ex}]")
        list.__init__(self,[])

        if isinstance(yml, dict):
            if "RUN" in yml:
                scenar = yml["RUN"]
                del yml["RUN"]
                conf = yml

                pycode.declare_methods(conf)
                self.env.update( **conf )

                self.extend( self._feed( scenar ) )
            else:
                raise ScenarException("No RUN section in scenario")
        elif isinstance(yml, list):
            scenar = yml
            conf={}
            self.extend( self._feed( scenar ) )

        else:
            raise ScenarException(f"[{self.file_path}] [Bad syntax] [scenario must be a dict or a list]")



    def _feed(self, liste:list) -> list[Step]:
        if not isinstance(liste, list):
            raise ScenarException(f"[{self.file_path}] [Bad syntax] [RUN must be a list]")

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
    
    async def execute(self,switch:str|None) -> AsyncGenerator:

        if switch:
            assert switch in dict(self.env.switchs), f"Unknown switch '{switch}'"
            self.env.update( self.env.switchs[switch] )


        for step in self:
            try:
                async for i in step.process(self.env):
                    yield i
            except Exception as ex:
                raise ScenarException(f"[{self.file_path}] [Error Step {step}] [{ex}]")

class Test:
    def __init__(self, file:str, conf:dict|None=None):
        self.scenario = Scenario(file,Env(**(conf or {})))

    async def run(self,switch:str|None=None) -> AsyncGenerator:
        async for r in self.scenario.execute( switch ):
            yield r
    
if __name__ == "__main__":
    ...
    # logging.basicConfig(level=logging.DEBUG)

    # async def run_a_test(f:str):
    #     t=Test(f)
    #     async for i in t.run():
    #         if i:
    #             print(f"{i.request.method} {i.request.url} -> {i.response.status_code}")
    #             for tr in i.tests:
    #                 print(" -",tr.ok and "OK" or "KO",":", tr.text)
    #             print()


    # # asyncio.run( run_a_test("examples/ok/simple.yml") )
    # asyncio.run( run_a_test("examples/ok/test1.yml") )
