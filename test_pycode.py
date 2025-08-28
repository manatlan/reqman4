import yaml
from src import pycode


def test_declare_methods():
    t="""

    toto:
        mymethod: |
            # assert ENV
            return x * 23
        myval: abc

    mymethod2: |
        # assert ENV
        return x * 42

    myval: 123
    """

    import yaml

    d=yaml.safe_load(t)

    pycode.declare_methods(d)

    assert d["mymethod2"]( 1 ) == 42    
    assert d["toto"]["mymethod"]( 1 ) == 23
    assert d["myval"] == 123
    assert d["toto"]["myval"] == "abc"