from src.env import Env, convert, MyList,jzon_dumps,httpx

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
    d=convert(data)
    assert d.coco == "VAL"
    assert d.liste[0] == 1
    assert d.liste[1] == 2
    assert d.liste[2].key == "val"
    assert len(d.liste) == 3
    
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

def test_substitute_in_object_at_constructor(): # bad idea
    e=Env( v=42 , val="hello <<v>>", dico={"kiki":"<<v*2>>"}, liste=[1,2,"<<v*3>>"] )
    # assert e["val"] == "hello 42"
    # assert e["dico"]["kiki"] == 84
    # assert e["liste"][2] == 126

    e=Env( v=42 , v2="<<v>>", val="hello <<v2>>" )
    # assert e["val"] == "hello 42"
