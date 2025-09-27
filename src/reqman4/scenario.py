# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import os
import time
import httpx
from typing import Any, AsyncGenerator

# reqman imports
from . import common
from .common import assert_syntax
from . import env
from . import ehttp


import logging
logger = logging.getLogger(__name__)

class OP:
    CALL="CALL"
    SET="SET"

class Step:
    params: list|str|None = None
    line: int|None = None
    
    async def process(self,e:env.Env) -> AsyncGenerator:
        ...

    def extract_params(self,e:env.Env) -> list:
        params=self.params
        if params is None:
            return [None]
        elif isinstance(params, str):
            # params is something like "<<myheaders()>>"" or <<myheaders>>
            params = e.substitute(params)

        assert_syntax( isinstance(params, list),"params must be a list of dict")
        assert_syntax( all( isinstance(p, dict) for p in params ),"params must be a list of dict")
        return e.substitute_in_object(params,True)


class StepCall(Step):
    def __init__(self, scenario: "Scenario", step: dict, env:env.Env, params:list|str|None=None, line:int|None=None):
        self.line = line
        self.scenario = scenario
        self.params = params
        self.steps=[]

        # extract step into local properties
        self.name = step[OP.CALL]

        assert_syntax( len(step.keys()) == 1, f"unknowns call'attributes: {list(step.keys())}")
        assert_syntax( isinstance(self.name, str),"CALL must be a string")
        assert_syntax( self.name in env,f"CALL references unknown scenario '{self.name}'")
        
        sub_scenar = env[self.name]
        assert_syntax( isinstance(sub_scenar, list),"CALL must reference a list of steps")

        self.steps = self.scenario._feed( env, sub_scenar )

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
            return f"Step CALL:{self.name} with PARAMS:{self.params}:\n"+s
        else:
            return f"Step CALL:{self.name}:\n"+s



class StepHttp(Step):
    def __init__(self, scenario: "Scenario", step: dict, params: list|str|None=None, line:int|None=None):
        self.line = line
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
        self.tests = step.get("tests",[])

        assert_syntax(isinstance(self.tests,list),"tests must be a list of strings")
        assert_syntax(all( isinstance(t,str) for t in self.tests ),"tests must be a list of strings")


    def _prepare_request(self, env: env.Env) -> tuple:
        url = env.substitute(self.url)
        root = env.get("root", "")
        if root and url.startswith("/"):
            url = root + url
        assert_syntax(url.startswith("http"), f"url must start with http, found {url}")

        headers = env.get("headers", {}) or {}
        headers.update(self.headers)
        headers = env.substitute_in_object(headers,True)
        # httpx requires header values to be strings, so convert them all
        headers = {k: str(v) for k, v in headers.items()}

        body = self.body
        if body:
            if isinstance(body, str):
                body = env.substitute(body)
            elif isinstance(body, (dict, list)):
                body = env.substitute_in_object(body,True)

        return url, headers, body

    async def _execute_request(self, env: env.Env, url: str, headers: dict, body: Any) -> httpx.Response:
        #print(f"Executing request: method={self.method}, url={url}, headers={headers}, body={body}")
        start = time.time()
        response = await ehttp.call(
            self.method,
            url,
            body,
            headers=httpx.Headers(headers),
            proxy=env.get("proxy", None),
            timeout=env.get("timeout", 60_000) or 60_000,  # 60 sec
        )
        diff_ms = round((time.time() - start) * 1000)
        env.set_R_response(response, diff_ms)
        return response

    def _process_response(self, enw: env.Env, response: httpx.Response) -> common.Result:
        results = []
        for t in self.tests:
            try:
                ok, dico = enw.eval(t, with_context=True)
                context = "Variables:\n"
                for k, v in dico.items():
                    context += f"  {k}: {env.jzon_dumps(v, indent=None)}\n"
                results.append(common.TestResult(bool(ok), t, context))
            except Exception as ex:
                logger.error(f"Can't eval test [{t}] : {ex}")
                results.append(common.TestResult(None, t, f"ERROR: {ex}"))

        doc = enw.substitute(self.doc, raise_error=False)
        return common.Result(response.request, response, results, doc=doc)

    async def process(self, e: env.Env) -> AsyncGenerator:
        e.resolv()  # try to resolv max variables in env, before running http test

        params = self.extract_params(e)

        for param in params:
            e.scope_update(param)

            url, headers, body = self._prepare_request(e)
            response = await self._execute_request(e, url, headers, body)
            yield self._process_response(e, response)

            e.scope_revert(param)


    def __repr__(self):
        if self.params:
            return f"Step {self.method}:{self.url} with PARAMS:{self.params}"
        else:   
            return f"Step {self.method}:{self.url}"

class StepSet(Step):
    def __init__(self, scenario: "Scenario", step:dict, line:int|None=None):
        self.line = line
        self.scenario = scenario

        assert_syntax( len(step) == 1,"SET cannot be used with other keys")
        dico = step[OP.SET]
        assert_syntax(isinstance(dico, dict),"SET must be a dictionary")
        self.dico = dico

    async def process(self,e:env.Env) -> AsyncGenerator:
        e.update( e.substitute_in_object(self.dico,True) )
        yield None

    def __repr__(self):
        return f"Step SET {self.dico}"



class Scenario(list):
    def __init__(self, file_path: str, is_compatibility:int=0):

        if file_path.startswith("http"):
            try:
                yml = common.get_url_content(file_path)
            except Exception as ex:
                raise common.RqException(f"[URI:{file_path}] [http error] [{ex}]")
        else:
            file_path = os.path.relpath(file_path)
            if os.path.isfile(file_path):
                yml = open(file_path, 'rb')
            else:
                raise common.RqException(f"[{file_path}] [File not found]")
        self.file_path = file_path

        list.__init__(self,[])

        try:
            self._ys = common.YScenario(yml,is_compatibility)
        except Exception as ex:
            raise common.RqException(f"[{file_path}] [Bad syntax] [{ex}]")

    @property
    def conf(self) -> common.Conf:
        return self._ys.conf

    @property
    def steps(self) -> list:
        return self._ys._steps

    def _feed(self, env:env.Env, liste:list[dict]) -> list[Step]:
        try:
            step=None
            assert_syntax(isinstance(liste, list),"RUN must be a list")

            ll = []
            for step in liste:
                line = step.lc.line if hasattr(step, 'lc') else None
                assert_syntax( isinstance(step, dict), f"Bad Dict {step}")
                
                if "params" in step:
                    params=step["params"]
                    del step["params"]
                else:
                    params=None

                if OP.SET in step:
                    assert_syntax( params is None, "params cannot be used with set")
                    ll.append( StepSet( self, step, line ) )
                else:
                    if OP.CALL in step:
                        ll.append( StepCall( self, step, env, params, line ) )
                    else:
                        if set(step.keys()) & ehttp.KNOWNVERBS:
                            ll.append( StepHttp( self, step, params, line ) )
                        else:
                            raise common.RqException(f"Bad Dict {step}")
            return ll
        except common.RqException as ex:
            # this is an ERROR at compilation time
            line_info = f":{step.lc.line+1}" if hasattr(step, 'lc') and step.lc else ""
            raise common.RqException(f"[{self.file_path}{line_info}] [Bad {step}] [{ex}]")
    
    def __repr__(self):
        return super().__repr__()
    
    async def execute(self,enw:env.Env,with_begin:bool=False,with_end:bool=False) -> AsyncGenerator:
        self.clear()
        self.extend( self._feed( enw, self.steps ) )
        step=None
        try:

            if with_begin and enw.get("BEGIN"):
                logger.debug("Execute BEGIN statement")
                async for i in StepCall(self, {OP.CALL:"BEGIN"}, enw).process(enw):
                    yield i

            for step in self:
                logger.debug("Execute STEP %s",step)
                async for i in step.process(enw):
                    yield i

            if with_end and enw.get("END"):
                logger.debug("Execute END statement")
                async for i in StepCall(self, {OP.CALL:"END"}, enw ).process(enw):
                    yield i

        except Exception as ex:
            # this is an ERROR at execution time
            line_info = f":{step.line+1}" if hasattr(step, 'line') and step.line else ""
            raise common.RqException(f"[{self.file_path}{line_info}] [Error {step}] [{ex}]")



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
