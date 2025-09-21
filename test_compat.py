
from src.reqman4 import compat,common

def test_fix_expr():
    # reqman
    assert compat._fix_expr("<<var>>") == "<<var>>"
    assert compat._fix_expr("{{var}}") == "<<var>>"
    assert compat._fix_expr("hello <<var>>") == "hello <<var>>"
    assert compat._fix_expr("hello {{var}}") == "hello <<var>>"
    assert compat._fix_expr("hello <<var|method1>>") == "hello <<method1(var)>>"
    assert compat._fix_expr("hello {{var|method1}}") == "hello <<method1(var)>>"
    assert compat._fix_expr("hello <<var|method1|m2>>") == "hello <<m2(method1(var))>>"
    assert compat._fix_expr("hello {{var|m1|m2}}") == "hello <<m2(m1(var))>>"

    # rq4
    assert compat._fix_expr("<<var * 'x'>>") == "<<var * 'x'>>"


def test_fix_tests_base():
    d=common.yload("""
tests:
    status: 200
    json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['R.status == 200', 'R.json.result == "ok"']

    d=common.yload("""
tests:
    status:
        - 200
        - 201
    json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['R.status in [200, 201]', 'R.json.result == "ok"']

    d=common.yload("""
tests:
    - status: 200
    - json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['R.status == 200', 'R.json.result == "ok"']

    d=common.yload("""
tests:
    - status:
        - 200
        - 201
    - json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['R.status in [200, 201]', 'R.json.result == "ok"']


def test_fix_tests_more():
    d=common.yload("""
tests:
    - content: hello
""")
    assert compat.fix_tests(d["tests"]) == ['R.content == "hello"'] # BAD by design

    d=common.yload("""
tests:
    - json.result1: <<val>>
    - json.result2: <<val|transform>>
""")
    assert compat.fix_tests(d["tests"]) == ['R.json.result1 == val', 'R.json.result2 == transform(val)']


def test_fix_tests_compatible_new_version():
    d=common.yload("""
tests:
    - R.status == 200
    - R.json.result == "ok"
""")
    assert compat.fix_tests(d["tests"]) == ['R.status == 200', 'R.json.result == "ok"']," ???"


def test_fix_tests_comparaison():
    d=common.yload("""
tests:
    status:    .>= 200
    status:    .>200 
    json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['R.status > 200', 'R.json.result == "ok"']

    d=common.yload("""
tests:
    - status:    .>= 200
    - status:    .>200 
    - json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['R.status >= 200', 'R.status > 200', 'R.json.result == "ok"']


def test_fix_tests_comparaison_more():
    d=common.yload("""
tests:
    - status:    .!= 200
    - status:    .  <=   200 
    - json.result: .? ok
    - json.result: . !? ko
""")
    assert compat.fix_tests(d["tests"]) == ['R.status != 200', 'R.status <= 200', '"ok" in R.json.result', '"ko" not in R.json.result']
