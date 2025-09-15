# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import os
import yaml
import httpx
from dataclasses import dataclass


REQMAN_CONF='reqman.conf'


class RqException(Exception): 
    pass

def assert_syntax( condition:bool, msg:str):
    if not condition: raise RqException( msg )


@dataclass
class TestResult:
    ok: bool|None        # bool with 3 states : see __repr__
    text : str
    ctx : str

    def __repr__(self):
        return {True:"OK",False:"KO",None:"BUG"}[self.ok]


@dataclass
class Result:
    request: httpx.Request
    response: httpx.Response
    tests: list[TestResult]
    file: str = ""
    doc: str = ""


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

def get_url_content(url:str) -> str:
    r=httpx.get(url)
    r.raise_for_status()
    return r.text

def load_scenar( yml_str: str) -> tuple[dict,list]:
    yml = yaml.safe_load(yml_str)

    if isinstance(yml, dict):
        # new reqman4 (yml is a dict, and got a RUN section)
        if "RUN" in yml:
            scenar = yml["RUN"]
            del yml["RUN"]

            return (yml,scenar)
        else:
            return (yml,[])
    elif isinstance(yml, list):
        # for simple compat, reqman4 can accept list (but no conf!)
        scenar = yml
        return ({},scenar)
    else:
        raise Exception("scenario must be a dict or a list]")

