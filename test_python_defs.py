from src.reqman4 import common
from src.reqman4 import env


def test_declare_methods():
    t="""

    toto:
        mymethod: |
            assert ENV
            return x * 23
        myval: abc

    mymethod2: |
        assert ENV
        return "hello"

    myval: 123
    """


    e=env.Env( **common.yload(t) )

    assert e["mymethod2"]() == "hello"          # call with no parameter !
    assert e["toto"]["mymethod"]( 1 ) == 23
    assert e["myval"] == 123
    assert e["toto"]["myval"] == "abc"          # call a dict of methods