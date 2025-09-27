# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################

import re
import json
from ruamel.yaml.comments import CommentedSeq as YList
"""
to be able to run old reqman files with new rq4 engine

TODO: redo better
"""
import logging
logger = logging.getLogger(__name__)

VERBS=["GET","POST","DELETE","PUT","HEAD","OPTIONS","TRACE","PATCH","CONNECT"]

def fix_scenar( conf:dict, steps:list ) -> tuple[dict,list]:
    new_steps=[]
    if isinstance(steps,list):
        while len(steps)>0:
            step = steps.pop(0)
            logger.info("compat, analyse:",step)
            if isinstance(step,dict) and len(step.keys()) == 1 and (list(step.keys())[0] not in ["call","break","if"]+VERBS+["SET","CALL"]):
                logger.info(" - FIX DECLARE PROC") 
                proc_name,content = list(step.items())[0]
                if isinstance(content,dict):
                    content = YList( content )
                _, conf[proc_name] = fix_scenar( conf, content )
            else:
                # new syntax compatible, de facto.
                if "SET" in step:
                    new_steps.append( step )
                    continue
                elif "CALL" in step:
                    new_steps.append( step )
                    continue

                # old non supported syntax
                elif "if" in step:
                    raise Exception("there is a 'if' ---> no conversion")
                elif "break" in step: # don't reuse break
                    logger.info(" - FIX break (remove it)") 

                # old call: to CALL:
                elif "call" in step:      #TODO: attention a doc tests foreach params !!!!
                    assert "tests" not in step, "no 'tests:' in CALL !"
                    assert "doc" not in step, "no 'doc:' in CALL !"
                    logger.info(" - FIX call") 
                    old=step["call"]
                    del step["call"]

                    if "foreach" in step: 
                        logger.info(" - FIX foreach") 
                        old=step["foreach"]
                        del step["foreach"]
                        params=dict(params=old)
                    else:
                        params={}

                    if isinstance(old,str):
                        old=[old]
                    for name in old:
                        new_steps.append( {**dict(CALL=name),**params} )

                # old http to new one
                elif set(step.keys()) & set(VERBS):
                    verb = list(set(step.keys()) & set(VERBS))[0]
                    if step[verb].startswith("+"):
                        step[verb]=step[verb][1:]

                    assert "query" not in step,"query compatility not available"

                    if "tests" in step:
                        logger.info(" - FIX tests") 
                        step["tests"] = fix_tests( step["tests"] )

                    if "foreach" in step: 
                        logger.info(" - FIX foreach") 
                        old=step["foreach"]
                        del step["foreach"]
                        step["params"] = old

                    if "save" in step:
                        save=step["save"]
                        del step["save"]
                        if isinstance(save,str):
                            save={ save: "<<R>>" }
                        else:
                            assert isinstance(save,dict)
                            assert all('|' not in k for k in save.keys()), "Keys in 'save' must not contain '|'"
                            save = {k:_fix_expr(v) for k,v in save.items()}

                    else:
                        save=None

                    new_steps.append( step )
                    if save:
                        new_steps.append( dict(SET=save) )
                    continue
                else:
                    raise Exception(f"what is this old step {step} ?")


    else:
        new_steps = steps
    return conf,new_steps

def _fix_name(k):
    if k in ["status","response.status","rm.response.status"]:
        k="R.status"
    elif k in ["content","response.content","rm.response.content"]:
        k="R.content"
    elif k.startswith("json."):
        k = "R.json"+k[4:]        
    elif k.startswith("response.json."):
        k = "R.json"+k[13:]        
    elif k.startswith("rm.response.json."):
        k = "R.json"+k[16:]        
    return k


def _fix_expr( text: str ) -> str:


    ll = re.findall(r"\{\{[^\}]+\}\}", text) + re.findall("<<[^><]+>>", text)
    for expr in ll:
        content = expr[2:-2]
        if "|" in content:
            parts = content.split("|")
            var = _fix_name(parts.pop(0))
            for method in parts:
                var = f"{method}({var})"
            text = text.replace(expr, f"<<{var}>>" )
        else:
            text = text.replace(expr, f"<<{_fix_name(content)}>>" )
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
        
        rk=_fix_name(k)

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


