import yaml
from src import env


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

    x=env.Env(**d)
    x.compile()

    assert x["mymethod2"]( 1 ) == 42    
    assert x["toto"]["mymethod"]( 1 ) == 23
    assert x["myval"] == 123
    assert x["toto"]["myval"] == "abc"