# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################

import re,json

"""
to be able to run old reqman files with new rq4 engine

TODO: redo better
"""
import yaml



def fix_scenar( conf:dict, steps:list ) -> tuple[dict,list]:
    #TODO: fix old reqman3 files
    # - declare sub_scenar in conf
    # - ensure params is list (or str)
    # - create a second step with "set"<-dict, where "save" is present
    # - "query" ?
    # - "foreach" ?

    return conf,steps


def _fix_expr( text: str ) -> str:
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

    def fix_comp(k:str,v) -> str:
        op = "=="

        if isinstance(v,str):
            g = re.match(r"^\. *([\?!=<>]{1,2}) *(.+)$", v)
            if g:
                op, v = g.groups()

                if op == "?":
                    op = "in"
                elif op == "!?":
                    op = "not in"

                try:
                    v=int(v)
                except:
                    pass

        if isinstance(v,str) and v.startswith("<<") and v.endswith(">>"):
            rv = _fix_expr(v)[2:-2]
        elif isinstance(v,str) and v.startswith("{{") and v.endswith("}}"):
            rv = _fix_expr(v)[2:-2]
        else:
            rv=json.dumps(v)
        if k == "status":
            rk="R.status"
        elif k == "content":
            rk="R.content"
        elif k.startswith("json."):
            rk = "R.json"+k[4:]

        if isinstance(v, list):
            return f"{rk} in {rv}"
        else:
            if op in ["in","not in"]:
                return f"{rv} {op} {rk}"
            else:
                return f"{rk} {op} {rv}"


    if isinstance(tests, dict):
        new_tests = []
        for k,v in tests.items():
            new_tests.append( fix_comp(k,v) )
        return new_tests
    elif isinstance(tests, list):
        new_tests = []
        for dico in tests:
            if isinstance(dico, str):
                new_tests.append( dico )
            elif isinstance(dico, dict):
                for k,v in dico.items():
                    new_tests.append( fix_comp(k,v) )
            else:
                raise Exception(f"Bad test item {dico}")
        return new_tests



if __name__ == "__main__":
    ...
    # assert fix_expr("{{var}}") == "<<var>>"


