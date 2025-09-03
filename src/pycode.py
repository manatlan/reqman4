# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
import logging
from types import CodeType

logger = logging.getLogger(__name__)


def is_python(k,v) -> CodeType|None:
    if type(v) == str and "return" in v:

        def declare(k:str,code:str) -> str:
            return f"def {k}(x=None):\n" + ("\n".join(["  " + i for i in code.splitlines()]))

        try:
            logger.info("*** DECLARE METHOD PYTHON: %s",k)
            return compile(declare(k,v), "unknown", "exec")
        except Exception as e:
            logging.error("Python Compilation Error : %s",e)
            return None

def declare_methods(d):
    if isinstance(d, dict):
        for k,v in d.items():
            code=is_python(k,v)
            if code:
                x={}
                exec(code, {},  x)
                d[k] = x[k]
            else:
                declare_methods(v)
    elif isinstance(d, list):
        for i in range(len(d)):
            declare_methods(d[i])


if __name__=="__main__":
    ...
    # logging.basicConfig(level=logging.DEBUG)

