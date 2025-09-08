# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import re,os
import httpx,json
import ast
from typing import Any
from dataclasses import dataclass
import logging

# reqman imports
from . import pycode
from .common import assert_syntax
from . import tool
from .ehttp import MyHeaders

logger = logging.getLogger(__name__)

@dataclass
class R:
    status: int
    headers: httpx.Headers
    content: bytes
    time: int

    @property
    def json(self):
        if self.content:
            return _convert( json.loads(self.content) )
        else:
            return {} # empty thing

    @property
    def text(self):
        if self.content:
            return self.content.decode()
        else:
            return ""

class MyDict(dict):
    def __init__(self, dico: dict):
        super().__init__(dico)
    def __getattr__(self, key):
        if "_" in key:
            okey = key.replace("_","-")
            if okey in self:
                return super().__getitem__(okey)
        return super().__getitem__(key)
    

class MyList(list):
    def __init__(self, liste: list):
        super().__init__(liste)

# transforme un objet python (pouvant contenir des dict et des list) en objet avec accès par attribut
def _convert(obj) -> Any:
    if isinstance(obj, dict):
        dico = {}
        for k,v in obj.items():
            dico[k]=_convert(v)
        return MyDict(dico)
    elif isinstance(obj, list):
        liste = []
        for v in obj:
            liste.append( _convert(v) )
        return MyList(liste)
    else:
        return obj

def jzon_dumps(o,indent:int|None=2):
    def default(obj):
        if callable(obj):
            return f"<function {getattr(obj, '__name__', str(obj))}>"
        elif isinstance(obj, httpx.Headers):
            return jzon_dumps(dict(obj))
        elif isinstance(obj, set):
            return jzon_dumps(list(obj))            
        elif isinstance(obj, Env):
            return jzon_dumps(obj._data)            
        elif isinstance(obj,R):
            return dict(status=obj.status, headers=dict(obj.headers), time=obj.time, content=f"<<{obj.content and len(obj.content) or '0'} bytes>>")
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
    return json.dumps(o, default=default, indent=indent)


class Env:
    def __init__(self, /, **kwargs):
        self._data:dict = _convert(kwargs)
        self._compile_py_methods()
        self.__params_scopes: list = []

    def __setitem__(self, key, value):
        self._data[key] = _convert(value)
        self._compile_py_methods()

    def update(self, dico):
        self._data.update(_convert(dico))
        self._compile_py_methods()


    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

    # def __delitem__(self, key):
    #     del self._data[key]

    # def keys(self):
    #     return self._data.keys()

    # def items(self):
    #     return self._data.items()

    # def values(self):
    #     return self._data.values()

    def eval(self, code: str, with_context: bool = False) -> Any:
        logger.debug(f"EVAL: {code}")
        if code in os.environ:
            return os.environ[code]

        env = dict(self._data)
        result = eval(code, {}, env)
        if with_context:
            try:
                vars_in_expr = {node.id for node in ast.walk(ast.parse(code)) if isinstance(node, ast.Name)}
                values = {var: env.get(var, None) for var in vars_in_expr}
            except Exception:
                values = {}
            return result, values
        else:
            return result

    def substitute(self, text: str, raise_error: bool = True) -> Any:
        """ resolve {{expr}} and/or <<expr>> in text 
            if raise_error==False : it will always return str (error msg)
        """ 
        ll = re.findall(r"\{\{[^\}]+\}\}", text) + re.findall("<<[^><]+>>", text)
        for l in ll:
            expr = l[2:-2]
            if raise_error:
                val = self.eval(expr)
            else:
                try:
                    val = self.eval(expr)
                except Exception as e:
                    val = f"***ERROR: {e}***"
            logger.debug(f"SUBSTITUTE {l} by {val} ({type(val)})")
            if isinstance(val, str):
                text = text.replace(l, val)
            else:
                if l == text:  # full same type
                    return val
                else:
                    # it's a part of a string, convert to str
                    # text = text.replace(l, str(val))
                    text = text.replace(l, jzon_dumps(val, indent=None))
        return text

    def substitute_in_object(self, o: Any) -> Any:
        def _sub_in_object(o: Any) -> Any:
            if isinstance(o, str):
                return self.substitute(o)
            elif isinstance(o, dict):
                return {k: _sub_in_object(v) for k, v in o.items()}
            elif isinstance(o, list):
                return [_sub_in_object(v) for v in o]
            else:
                return o

        while True:
            before = jzon_dumps(o)
            o = _sub_in_object(o)
            after = jzon_dumps(o)
            if before == after:
                return o

    @property
    def switchs(self) -> dict:
        d = {}
        for i in ["switch", "switches", "switchs"]:   #TODO: compat rq & reqman
            if i in self._data:
                switchs = self._data.get(i, {})
                assert_syntax(isinstance(switchs, dict), "switch must be a dictionary")
                for k, v in switchs.items():
                    assert_syntax(isinstance(v, dict), "switch item must be a dictionary")
                    d[k] = v
                return d
        return d

    def set_R_response(self, response: httpx.Response, time):
        self._data["R"] = R(response.status_code, MyHeaders(response.headers), response.content, time)

    #/-------------------------------------------------
    def scope_update(self, params: dict):
        # save current same keys, revert with scope_revert()
        if params:
            self.__params_scopes.append({k: self._data.get(k, None) for k in params.keys()})
            self.update(params)

    def scope_revert(self, params: dict):
        # revert inserted params with scope_update()
        if params:
            if self.__params_scopes:
                scope = self.__params_scopes.pop()
                for k, v in scope.items():
                    # restore the same keys before scope_update()
                    if v is None:
                        del self._data[k]
                    else:
                        self._data[k] = v
    #\-------------------------------------------------

    def _compile_py_methods(self):
        """ Compile python method found in the dict and children """
        def declare_methods(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    code = pycode.is_python(k, v)
                    if code:
                        scope = {}
                        exec(code, dict(ENV=self, tool=tool), scope)  # declare ENV&tool in method!
                        d[k] = scope[k]
                    else:
                        declare_methods(v)
            elif isinstance(d, list):
                for i in range(len(d)):
                    declare_methods(d[i])
        declare_methods(self._data)

if __name__ == "__main__":
    ...
    # logging.basicConfig(level=logging.DEBUG)

    # e=Env( method = lambda x: x * 39 )
    # x=e.eval("method(3)")
    # assert x == 117
