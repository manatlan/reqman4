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

# reqman imports
from common import RqException

logger = logging.getLogger(__name__)


def is_python(k,v) -> CodeType|None:
    if type(v) == str and "return" in v:

        def declare(k:str,code:str) -> str:
            return f"def {k}(x=None):\n" + ("\n".join(["  " + i for i in code.splitlines()]))

        try:
            logger.info("*** DECLARE METHOD PYTHON: %s",k)
            return compile(declare(k,v), f"method '{k}'", "exec")
        except Exception as e:
            raise RqException(f"Python Compilation Error : {e}")


if __name__=="__main__":
    ...
    # logging.basicConfig(level=logging.DEBUG)

