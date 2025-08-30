import yaml
from src import compat

def test_fix_expr():
    # reqman
    assert compat.fix_expr("<<var>>") == "<<var>>"
    assert compat.fix_expr("{{var}}") == "<<var>>"
    assert compat.fix_expr("hello <<var>>") == "hello <<var>>"
    assert compat.fix_expr("hello {{var}}") == "hello <<var>>"
    assert compat.fix_expr("hello <<var|method1>>") == "hello <<method1(var)>>"
    assert compat.fix_expr("hello {{var|method1}}") == "hello <<method1(var)>>"
    assert compat.fix_expr("hello <<var|method1|m2>>") == "hello <<m2(method1(var))>>"
    assert compat.fix_expr("hello {{var|m1|m2}}") == "hello <<m2(m1(var))>>"

    # rq4
    assert compat.fix_expr("<<var * 'x'>>") == "<<var * 'x'>>"


def test_fix_tests_base():
    d=yaml.safe_load("""
tests:
    status: 200
    json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['$status == 200', '$.result == "ok"']

    d=yaml.safe_load("""
tests:
    status:
        - 200
        - 201
    json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['$status in [200, 201]', '$.result == "ok"']

    d=yaml.safe_load("""
tests:
    - status: 200
    - json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['$status == 200', '$.result == "ok"']

    d=yaml.safe_load("""
tests:
    - status:
        - 200
        - 201
    - json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['$status in [200, 201]', '$.result == "ok"']


def test_fix_tests_more():
    d=yaml.safe_load("""
tests:
    - content: hello
""")
    assert compat.fix_tests(d["tests"]) == ['$ == "hello"']

    d=yaml.safe_load("""
tests:
    - json.result1: <<val>>
    - json.result2: <<val|transform>>
""")
    assert compat.fix_tests(d["tests"]) == ['$.result1 == val', '$.result2 == transform(val)']


def test_fix_tests_compatible_new_version():
    d=yaml.safe_load("""
tests:
    - $status == 200
    - $.result == "ok"
""")
    assert compat.fix_tests(d["tests"]) == ['$status == 200', '$.result == "ok"']," ???"


def test_fix_tests_comparaison():
    d=yaml.safe_load("""
tests:
    status:    .>= 200
    status:    .>200 
    json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['$status > 200', '$.result == "ok"']

    d=yaml.safe_load("""
tests:
    - status:    .>= 200
    - status:    .>200 
    - json.result: ok
""")
    assert compat.fix_tests(d["tests"]) == ['$status >= 200', '$status > 200', '$.result == "ok"']


def test_fix_tests_comparaison_more():
    d=yaml.safe_load("""
tests:
    - status:    .!= 200
    - status:    .  <=   200 
    - json.result: .? ok
    - json.result: . !? ko
""")
    assert compat.fix_tests(d["tests"]) == ['$status != 200', '$status <= 200', '"ok" in $.result', '"ko" not in $.result']
