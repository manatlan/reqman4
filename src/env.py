# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
import re,os
import httpx,json

import logging
logger = logging.getLogger(__name__)

class MyDict(dict):
    def __init__(self, dico: dict):
        super().__init__(dico)
    def __getattr__(self, key):
        return super().__getitem__(key)
class MyList(list):
    def __init__(self, liste: list):
        super().__init__(liste)

# transforme un objet python (pouvant contenir des dict et des list) en objet avec accès par attribut
def convert(obj):
    if isinstance(obj, dict):
        dico = {}
        for k,v in obj.items():
            dico[k]=convert(v)
        return MyDict(dico)
    elif isinstance(obj, list):
        liste = []
        for v in obj:
            liste.append( convert(v) )
        return MyList(liste)
    else:
        return obj

def jzon_dumps(o):
    def default(obj):
        if callable(obj):
            return f"<function {getattr(obj, '__name__', str(obj))}>"
        elif isinstance(obj, httpx.Headers):
            return jzon_dumps(dict(obj))
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
    return json.dumps(o, default=default, indent=2)

class Env(dict):
    def __init__(self, /, **kwargs):
        super().__init__(**kwargs)
        # self.update( self.substitute_in_object(self) )    # <- not a good idea
    
    def eval(self, code: str) -> any:
        logger.debug(f"EVAL: {code}")
        if code in os.environ:
            return os.environ[code]
        else:
            code = code.replace("$.","_.")
            code = code.replace("$status","_status")
            code = code.replace("$headers","_headers")
            code = code.replace("$","_")
        return eval(code,{}, dict(self) )

    def substitute(self, text: str) -> any:
        """ resolve {{expr}} and/or <<expr>> in text """
        ll = re.findall(r"\{\{[^\}]+\}\}", text) + re.findall("<<[^><]+>>", text)
        for l in ll:
            expr = l[2:-2]
            val = self.eval(expr)
            logger.debug(f"SUBSTITUTE {l} by {val} ({type(val)})")
            if isinstance(val, str):
                text = text.replace(l, val)
            else:
                if l==text: # full same type
                    return val
                else:
                    # it's a part of a string, convert to str
                    text = text.replace(l, str(val))
        return text

    def substitute_in_object(self, o: any) -> any:
        def _sub_in_object( o: any) -> any:
            if isinstance(o, str):
                return self.substitute(o)
            elif isinstance(o, dict):
                return {k:_sub_in_object(v) for k,v in o.items()}
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
        d={}
        for i in ["switch","switches","switchs"]:   #TODO: compat rq & reqman
            if i in self:
                switchs = self.get(i,{})
                assert isinstance(switchs, dict), "switch must be a dictionary"
                for k,v in switchs.items():
                    assert isinstance(v, dict), "switch item must be a dictionary"
                    d[k]=v
                return d
        return d


    def setHttpResonse(self, response:httpx.Response): 

        try:
            # json content ?
            content = json.loads(response.content)
        except:
            try:
                # text content ?
                content = response.content.decode()
            except:
                # byte content !
                content = response.content


        self["_status"]=response.status_code
        self["_"]=convert(content)
        self["_headers"]=response.headers

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    e=Env( method = lambda x: x * 39 )
    x=e.eval("method(3)")
    assert x == 117
