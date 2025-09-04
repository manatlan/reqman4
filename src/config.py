# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
from common import assert_syntax
import os
import yaml

REQMAN_CONF='reqman.conf'

# special keys :

# proxy: <string>
# timeout: <milliseconds>
# root: <string> 
# switchs: <dict/mapping>


def guess_reqman_conf(paths:list[str]) -> str|None:
    if paths:
        cp = os.path.commonpath([os.path.dirname(os.path.abspath(p)) for p in paths])

        rqc = None
        while os.path.basename(cp) != "":
            if os.path.isfile(os.path.join(cp, REQMAN_CONF)):
                rqc = os.path.join(cp, REQMAN_CONF)
                break
            else:
                cp = os.path.realpath(os.path.join(cp, os.pardir))
        return rqc

def load_reqman_conf(path:str) -> dict:
    with open(path, 'r') as f:
        conf = yaml.load( f, Loader=yaml.SafeLoader)
    assert_syntax( isinstance(conf, dict) , "reqman.conf must be a mapping")
    return conf
