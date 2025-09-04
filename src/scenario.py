# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
from exceptions import CheckSyntaxError
import yaml,os,time
from dataclasses import dataclass
import httpx
from typing import AsyncGenerator

from env import Env,R
import ehttp
import compat

import logging
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    ok: bool|None        # bool with 3 states : see __repr__
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

        if not isinstance(params, list): raise CheckSyntaxError("params must be a list of dict")
        if not all( isinstance(p, dict) for p in params ): raise CheckSyntaxError("params must be a list of dict")
        return params


class StepCall(Step):
    def __init__(self, scenario: "Scenario", step: dict, params:list|str|None=None):
        self.scenario = scenario
        self.params = params

        # extract step into local properties
        name = step["call"]

        if not isinstance(name, str): raise CheckSyntaxError("CALL must be a string")
        if not name in self.scenario.env: raise CheckSyntaxError(f"CALL references unknown scenario '{name}'")
        
        sub_scenar = self.scenario.env[name]
        if not isinstance(sub_scenar, list): raise CheckSyntaxError("CALL must reference a list of steps")

        self.steps = self.scenario._feed( sub_scenar )

    async def process(self,e:Env) -> AsyncGenerator:

        params=self.extract_params(e) 

        for param in params:
            if param:
                e.scope_update(param)

            for step in self.steps:
                async for r in step.process(e): # type: ignore
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
        if not len(methods) == 1: raise CheckSyntaxError(f"Step must contain exactly one HTTP method, found {methods}")
        method = methods.pop()
        self.method = method
        self.url = step[method]
        self.doc = step.get("doc","")
        self.headers = step.get("headers",{})
        self.body = step.get("body",None)
        self.tests = compat.fix_tests( step.get("tests",[]) )
        if not isinstance(self.tests,list): raise CheckSyntaxError("tests must be a list of strings")
        if not all( isinstance(t,str) for t in self.tests ): raise CheckSyntaxError("tests must be a list of strings")


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
            if not url.startswith("http"): raise CheckSyntaxError(f"url must start with http, found {url}")
                
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
            e.set_R_response( response, diff_ms )
            
            
            results=[]
            for t in self.tests:
                try:
                    ok, dico = e.eval(t, with_context=True)
                    context=""
                    for k,v in dico.items():
                        if k=="R":      #TODO: do better !
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
                    logger.error(f"Can't eval test [{t}] : {ex}")
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

        if not len(step) == 1: raise CheckSyntaxError("SET cannot be used with other keys")
        dico = step["set"]
        if not isinstance(dico, dict): raise CheckSyntaxError("SET must be a dictionary")
        self.dico = dico

    async def process(self,e:Env) -> AsyncGenerator:
        e.update( self.dico )
        e.update( e.substitute_in_object(self.dico) )
        yield None

    def __repr__(self):
        return f"SET {self.dico}"

class ScenarException(Exception): pass

class Scenario(list):
    def __init__(self, file_path: str, conf:dict|None=None):
        try:
            self.env=Env(**(conf or {}))
        except Exception as e:
            raise ScenarException(f"[{file_path}] [{e}]")

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

                try:
                    self.env.update( conf )
                except Exception as e:
                    raise ScenarException(f"[{self.file_path}] [{e}]")

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
                if not isinstance(step, dict): raise CheckSyntaxError(f"Bad step {step}")
                
                if "params" in step:
                    params=step["params"]
                    del step["params"]
                else:
                    params=None

                if "set" in step:
                    if not params is None: raise CheckSyntaxError("params cannot be used with set")
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
        except CheckSyntaxError as ex:
            raise ScenarException(f"[{self.file_path}] [Bad step {step}] [{ex}]")
    
    def __repr__(self):
        return super().__repr__()
    
    async def execute(self,switch:str|None=None) -> AsyncGenerator:

        if switch:
            if not switch in dict(self.env.switchs): raise CheckSyntaxError(f"Unknown switch '{switch}'")
            self.env.update( self.env.switchs[switch] )

        for step in self:
            try:
                async for i in step.process(self.env):
                    yield i
            except Exception as ex:
                raise ScenarException(f"[{self.file_path}] [Error Step {step}] [{ex}]")


    
if __name__ == "__main__":
    ...
    # logging.basicConfig(level=logging.DEBUG)

    # async def run_a_test(f:str):
    #     t=Scenario(f)
    #     async for i in t.execute():
    #         if i:
    #             print(f"{i.request.method} {i.request.url} -> {i.response.status_code}")
    #             for tr in i.tests:
    #                 print(" -",tr.ok and "OK" or "KO",":", tr.text)
    #             print()


    # # asyncio.run( run_a_test("examples/ok/simple.yml") )
    # asyncio.run( run_a_test("examples/ok/test1.yml") )
