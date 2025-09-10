import pytest
from src.reqman4.env import Env, _convert, MyList,jzon_dumps,httpx

def test_jzon_dumps():
    assert jzon_dumps( dict(method = lambda x: x * 39,headers=httpx.Headers() ) )

def test_eval_python_call():
    e=Env( method = lambda x: x * 39 )
    x=e.eval("method(3)")
    assert x == 117

def test_eval_status():
    e=Env( status = 200)
    x=e.eval("status == 200")
    assert x is True


def test_mylist():
    liste=[1,2,{"key":"val"}]
    l=MyList(liste)
    assert len(l) == 3

def test_convert():
    data={
        "coco":"VAL",
        "liste":[1,2,{"key":"val"}],
    }
    d=_convert(data)
    assert d.coco == "VAL" # type: ignore
    assert d.liste[0] == 1 # type: ignore
    assert d.liste[1] == 2 # type: ignore
    assert d.liste[2].key == "val" # type: ignore
    assert len(d.liste) == 3 # type: ignore
    
def test_substitute():
    e=Env( v=42 )
    assert e.substitute("val is {{v}}") == "val is 42"
    assert e.substitute("val is <<v>>") == "val is 42"
    assert e.substitute("val is <<v*2>>") == "val is 84"

    assert e.substitute("<<v>>") == 42  # full same type !


def test_dotenv():
    import os
    un = os.environ["USER"]
    e=Env()
    assert e.substitute("<<USER>>")==un
    assert e.eval("USER")==un

def test_substitute_in_object():
    e=Env( v=42 )
    d=dict( kiki="<< v*2 >>" )
    d=e.substitute_in_object(d)
    assert d["kiki"] == 84

def test_inc():
    e=Env( v=1 )
    assert e["v"]==1
    e["v"]=e.substitute("<<v + 1>>")
    assert e["v"]==2

    e=Env( v=1 )
    assert e["v"]==1
    d=dict( v="<< v+1 >>" )
    e=e.substitute_in_object(d)
    assert e["v"]==2


def test_complexe():
    e=Env( users=dict(u1=dict(name="marco")) )
    assert e["users"]["u1"]["name"]=="marco"
    assert e["users"].u1.name=="marco"  # type: ignore   #dict access by attrs

    e["default1"]=e.substitute("<<users.u1>>")
    assert e["default1"].name == "marco"

    e["default2"]=e.eval("users.u1")
    assert e["default2"].name == "marco"


@pytest.mark.skip()
def test_complexe2():
    e=Env( default="<<users.u2>>", users=dict(u1=dict(name="marco")) )
    assert e["default"] == "<<users.u2>>"

    e=Env( default="<<users.u1>>", users=dict(u1=dict(name="marco")) )
    assert e["default"] == {"name":"marco"}
    


def test_substitute_in_object_at_constructor(): # bad idea
    e=Env( v=42 , val="hello <<v>>", dico={"kiki":"<<v*2>>"}, liste=[1,2,"<<v*3>>"] )
    # assert e["val"] == "hello 42"
    # assert e["dico"]["kiki"] == 84
    # assert e["liste"][2] == 126

    e=Env( v=42 , v2="<<v>>", val="hello <<v2>>" )
    # assert e["val"] == "hello 42"


def test_protect_scope():
    d = Env(**dict(a=42, b=list("abc"), z=1, x=dict(z=1,l=list("AZ"))))

    assert d["a"]==42
    assert d["z"]==1
    assert d["x"]==dict(z=1,l=list("AZ"))

    # update dict
    param = dict(z=99,x=dict(z=2,l=list("ZA")))
    d.scope_update( param )
    assert d["a"]==42
    assert d["z"]==99
    assert d["x"]==dict(z=2,l=list("ZA"))

    print(jzon_dumps(d))

    # revert all before update ^
    d.scope_revert( param )
    assert d["a"]==42
    assert d["z"]==1
    assert d["x"]==dict(z=1,l=list("AZ"))    

if __name__=="__main__":
    ...      
    test_complexe2()