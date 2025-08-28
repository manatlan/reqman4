import re,yaml,json

"""
to be able to run old reqman files with new rq4 engine

**IN CONSTRUCTION** (not used yet)

"""

def fix_expr( text: str ) -> str:
    ll = re.findall(r"\{\{[^\}]+\}\}", text) + re.findall("<<[^><]+>>", text)
    for expr in ll:
        content = expr[2:-2]
        if "|" in content:
            parts = content.split("|")
            var = parts.pop(0)
            for method in parts:
                var = f"{method}({var})"
            text = text.replace(expr, f"<<{var}>>" )
        else:
            text = text.replace(expr, f"<<{content}>>" )
    return text

def fix_tests(tests:dict|list) -> list[str]:

    def fix_comp(k:str,v:any) -> str:
        rv=json.dumps(v)
        if k == "status":
            rk="$status"
        elif k == "content":
            rk="$"
        elif k.startswith("json."):
            rk = "$"+k[4:]

        if isinstance(v, list):
            return f"{rk} in {rv}"
        else:
            return f"{rk} == {rv}"


    if isinstance(tests, dict):
        new_tests = []
        for k,v in tests.items():
            new_tests.append( fix_comp(k,v) )
        return new_tests
    elif isinstance(tests, list):
        new_tests = []
        for dico in tests:
            for k,v in dico.items():
                new_tests.append( fix_comp(k,v) )
        return new_tests

if __name__ == "__main__":
    # reqman
    assert fix_expr("<<var>>") == "<<var>>"
    assert fix_expr("{{var}}") == "<<var>>"
    assert fix_expr("hello <<var>>") == "hello <<var>>"
    assert fix_expr("hello {{var}}") == "hello <<var>>"
    assert fix_expr("hello <<var|method1>>") == "hello <<method1(var)>>"
    assert fix_expr("hello {{var|method1}}") == "hello <<method1(var)>>"
    assert fix_expr("hello <<var|method1|m2>>") == "hello <<m2(method1(var))>>"
    assert fix_expr("hello {{var|m1|m2}}") == "hello <<m2(m1(var))>>"

    # rq4
    assert fix_expr("<<var * 'x'>>") == "<<var * 'x'>>"


    d=yaml.safe_load("""
tests:
    status: 200
    json.result: ok
""")
    assert fix_tests(d["tests"]) == ['$status == 200', '$.result == "ok"']

    d=yaml.safe_load("""
tests:
    status:
        - 200
        - 201
    json.result: ok
""")
    assert fix_tests(d["tests"]) == ['$status in [200, 201]', '$.result == "ok"']

    d=yaml.safe_load("""
tests:
    - status: 200
    - json.result: ok
""")
    assert fix_tests(d["tests"]) == ['$status == 200', '$.result == "ok"']

    d=yaml.safe_load("""
tests:
    - status:
        - 200
        - 201
    - json.result: ok
""")
    assert fix_tests(d["tests"]) == ['$status in [200, 201]', '$.result == "ok"']

    d=yaml.safe_load("""
tests:
    - content: hello
""")
    assert fix_tests(d["tests"]) == ['$ == "hello"']

    d=yaml.safe_load("""
tests:
    - json.result: <<val>>
    - json.result: <<val|transform>>
""")
    print( fix_tests(d["tests"]) )
    assert fix_tests(d["tests"]) == ['$.result == val']
