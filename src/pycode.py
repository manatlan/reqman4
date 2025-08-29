# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
import logging
logger = logging.getLogger(__name__)


def declare(k:str,code:str) -> str:
    return f"def {k}(x):\n" + ("\n".join(["  " + i for i in code.splitlines()]))

def is_python(x):
    if type(x) == str and "return" in x:
        try:
            return compile(declare("just_for_test",x), "unknown", "exec") and True
        except:
            return False

def declare_methods(d):
    if isinstance(d, dict):
        for k,v in d.items():
            if is_python(v):
                logger.info("*** DECLARE METHOD PYTHON: %s",k)
                src= declare(k,v)
                code = compile( src , "unknown", "exec")
                x={}
                exec(code, {},  x)
                d[k] = x[k]
            else:
                declare_methods(v)
    elif isinstance(d, list):
        for i in range(len(d)):
            declare_methods(d[i])


if __name__=="__main__":
    logging.basicConfig(level=logging.DEBUG)

