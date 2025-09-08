# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import yaml,os,time
import httpx
from typing import AsyncGenerator

# reqman imports
import common
from common import assert_syntax
import env
import ehttp


import compat
FIX_SCENAR = compat.fix_scenar
FIX_TESTS = compat.fix_tests

import logging
logger = logging.getLogger(__name__)



class Step:
    params: list|str|None = None
    
    async def process(self,e:env.Env) -> AsyncGenerator:
        ...

    def extract_params(self,e:env.Env) -> list:
        params=self.params
        if params is None:
            return [None]
        elif isinstance(params, str):
            params = e.substitute(params)

        assert_syntax( isinstance(params, list),"params must be a list of dict")
        assert_syntax( all( isinstance(p, dict) for p in params ),"params must be a list of dict")
        return params


class StepCall(Step):
    def __init__(self, scenario: "Scenario", step: dict, params:list|str|None=None):
        self.scenario = scenario
        self.params = params

        # extract step into local properties
        name = step["call"]

        assert_syntax( len(step.keys()) == 1, f"unknowns call'attributes: {list(step.keys())}")
        assert_syntax( isinstance(name, str),"CALL must be a string")
        assert_syntax( name in self.scenario.env,f"CALL references unknown scenario '{name}'")
        
        sub_scenar = self.scenario.env[name]
        assert_syntax( isinstance(sub_scenar, list),"CALL must reference a list of steps")

        self.steps = self.scenario._feed( sub_scenar )

    async def process(self,e:env.Env) -> AsyncGenerator:

        params=self.extract_params(e) 

        for param in params:
            e.scope_update(param)

            for step in self.steps:
                async for r in step.process(e): # type: ignore
                    yield r

            e.scope_revert(param)

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
        assert_syntax( len(methods) == 1,f"Step must contain exactly one HTTP method, found {methods}")
        method = methods.pop()
        attributs = set(step.keys()) - set([method])

        assert_syntax( not attributs - {"doc","headers","body","tests"},f"unknowns http'attributes {list(step.keys())}")

        self.method = method
        self.url = step[method]
        self.doc = step.get("doc","")
        self.headers = step.get("headers",{})
        self.body = step.get("body",None)
        self.tests = FIX_TESTS( step.get("tests",[]) )

        assert_syntax(isinstance(self.tests,list),"tests must be a list of strings")
        assert_syntax(all( isinstance(t,str) for t in self.tests ),"tests must be a list of strings")


    async def process(self,e:env.Env) -> AsyncGenerator:
        self.results=[]

        params=self.extract_params(e)

        for param in params:
            e.scope_update(param)

            url = e.substitute(self.url)
            root = e.get("root","")
            if root:
                if url.startswith("/"):
                    url = root + url
            assert_syntax( url.startswith("http"), f"url must start with http, found {url}")
                
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
                                r:env.R=e["R"]
                                k,v="R.time",r.time
                            if "R.status" in t:
                                r:env.R=e["R"]
                                k,v="R.status",r.status
                            if "R.headers" in t:
                                r:env.R=e["R"]
                                k,v="R.headers",r.headers
                            if "R.content" in t:
                                r:env.R=e["R"]
                                k,v="R.content",r.content
                            if "R.text" in t:
                                r:env.R=e["R"]
                                k,v="R.text",r.text
                            if "R.json" in t:
                                r:env.R=e["R"]
                                k,v="R.json",r.json
                            
                        context+= f"{k}: {v}\n"
                    results.append( common.TestResult(bool(ok),t,context) )
                except Exception as ex:
                    logger.error(f"Can't eval test [{t}] : {ex}")
                    results.append( common.TestResult(None,t,f"ERROR: {ex}") )


            doc=e.substitute(self.doc)
            yield common.Result(response.request,response, results, doc=doc)

            e.scope_revert(param)

    

    def __repr__(self):
        if self.params:
            return f"HTTP MULTIPLE {self.method} {self.url} with {self.params}"
        else:   
            return f"HTTP {self.method} {self.url}"

class StepSet(Step):
    def __init__(self, scenario: "Scenario", step:dict):
        self.scenario = scenario

        assert_syntax( len(step) == 1,"SET cannot be used with other keys")
        dico = step["set"]
        assert_syntax(isinstance(dico, dict),"SET must be a dictionary")
        self.dico = dico

    async def process(self,e:env.Env) -> AsyncGenerator:
        e.update( e.substitute_in_object(self.dico) )
        yield None

    def __repr__(self):
        return f"SET {self.dico}"



class Scenario(list):
    def __init__(self, file_path: str, e:env.Env|None=None):
        if e:
            assert isinstance(e,env.Env)
        else:
            e=env.Env()

        self.env = e

        if file_path.startswith("http"):
            try:
                yml_str = common.get_url_content(file_path)
            except Exception as ex:
                raise common.RqException(f"[URI:{file_path}] [http error] [{ex}]")
        else:
            if os.path.isfile(file_path):
                with open(file_path, 'r') as fid:
                    yml_str = fid.read()
            else:
                raise common.RqException(f"[{file_path}] [File not found]")
        self.file_path = file_path

        list.__init__(self,[])

        try:
            conf,scenar = common.load_scenar(yml_str)
            conf,scenar = FIX_SCENAR( conf, scenar)
        except yaml.YAMLError as ex:
            raise common.RqException(f"[{file_path}] [Bad syntax] [{ex}]")

        self.env.update( env.convert(conf) ) # this override a reqman.conf env !
        self.extend( self._feed( scenar ) )


    def _feed(self, liste:list) -> list[Step]:
        try:
            step=None
            assert_syntax(isinstance(liste, list),"RUN must be a list")

            ll = []
            for step in liste:
                assert_syntax( isinstance(step, dict), f"Bad step {step}")
                
                if "params" in step:
                    params=step["params"]
                    del step["params"]
                else:
                    params=None

                if "set" in step:
                    assert_syntax( params is None, "params cannot be used with set")
                    ll.append( StepSet( self, step ) )
                else:
                    if "call" in step:
                        ll.append( StepCall( self, step, params ) )
                    else:
                        if set(step.keys()) & ehttp.KNOWNVERBS:
                            ll.append( StepHttp( self, step, params ) )
                        else:
                            raise common.RqException(f"Bad step {step}")
            return ll
        except common.RqException as ex:
            raise common.RqException(f"[{self.file_path}] [Bad step {step}] [{ex}]")
    
    def __repr__(self):
        return super().__repr__()
    
    async def execute(self,with_begin:bool=False,with_end:bool=False) -> AsyncGenerator:
        try:

            if with_begin and self.env.get("BEGIN"):
                logger.debug("Execute BEGIN statement")
                async for i in StepCall(self, dict(call="BEGIN")).process(self.env):
                    yield i

            for step in self:
                async for i in step.process(self.env):
                    yield i

            if with_end and self.env.get("END"):
                logger.debug("Execute END statement")
                async for i in StepCall(self, dict(call="END")).process(self.env):
                    yield i

        except Exception as ex:
            raise common.RqException(f"[{self.file_path}] [Error Step {step}] [{ex}]")



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
