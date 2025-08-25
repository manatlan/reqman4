
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


class Env(dict):
    def __init__(self, /, **kwargs):
        super().__init__(**kwargs)
        self.update( self.substitute_in_object(self) )
    
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
            def default(obj):
                if callable(obj):
                    return f"<function {getattr(obj, '__name__', str(obj))}>"
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
            before = json.dumps(o, default=default)
            o = _sub_in_object(o)
            after = json.dumps(o, default=default)
            
            if before == after:
                return o

    


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

    e=Env( status = 200)
    x=e.eval("status == 200")
    assert x is True

    liste=[1,2,{"key":"val"}]
    l=MyList(liste)
    assert len(l) == 3

    data={
        "coco":"VAL",
        "liste":[1,2,{"key":"val"}],
    }
    d=convert(data)
    assert d.coco == "VAL"
    assert d.liste[0] == 1
    assert d.liste[1] == 2
    assert d.liste[2].key == "val"
    assert len(d.liste) == 3
    
    e=Env( v=42 )
    assert e.substitute("val is {{v}}") == "val is 42"
    assert e.substitute("val is <<v>>") == "val is 42"
    assert e.substitute("val is <<v*2>>") == "val is 84"

    assert e.substitute("<<v>>") == 42  # full same type !


    e=Env()
    assert e.substitute("<<USERNAME>>")=="manatlan"
    assert e.eval("USERNAME")=="manatlan"

    e=Env( v=42 )
    d=dict( kiki="<< v*2 >>" )
    d=e.substitute_in_object(d)
    assert d["kiki"] == 84

    e=Env( v=42 , val="hello <<v>>", dico={"kiki":"<<v*2>>"}, liste=[1,2,"<<v*3>>"] )
    assert e["val"] == "hello 42"
    assert e["dico"]["kiki"] == 84
    assert e["liste"][2] == 126

    e=Env( v=42 , v2="<<v>>", val="hello <<v2>>" )
    assert e["val"] == "hello 42"
