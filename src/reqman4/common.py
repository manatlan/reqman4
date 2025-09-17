# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import os
from ruamel.yaml import YAML
import httpx
from dataclasses import dataclass

yaml = YAML(typ='safe')
yaml.allow_duplicate_keys = True


REQMAN_CONF='reqman.conf'


class RqException(Exception):
    def __init__(self, msg:str, item=None):
        self.msg = msg
        self.item = item
        self.filename = None
        self.lineno = None
        if item and hasattr(item,"lc") and item.lc:
            self.lineno = item.lc.line + 1
        super().__init__(msg)

    def __str__(self):
        if self.filename and self.lineno:
            return f"{self.msg} in {self.filename} at line {self.lineno}"
        elif self.filename:
            return f"{self.msg} in {self.filename}"
        else:
            return self.msg

def assert_syntax( condition:bool, msg:str, item=None):
    if not condition:
        raise RqException( msg, item=item )


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


def find_scenarios(path_folder: str, filters=(".yml", ".rml")):
    for folder, subs, files in os.walk(path_folder):
        if (folder in [".", ".."]) or ( not os.path.basename(folder).startswith((".", "_"))):
            for filename in files:
                if filename.lower().endswith(
                    filters
                ) and not filename.startswith((".", "_")):
                    yield os.path.join(folder, filename)

def expand_files(files:list[str]) -> list[str]:
    """ Expand files list : if a directory is found, extract all scenarios from it """
    ll=[]
    for i in files:
        if os.path.isdir(i):
            ll.extend( list(find_scenarios(i)) )
        else:
            ll.append(i)
    return ll

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
        content = f.read()
    conf = yaml.load( content )
    assert_syntax( isinstance(conf, dict) , "reqman.conf must be a mapping", item=conf)
    return conf

def get_url_content(url:str) -> str:
    r=httpx.get(url)
    r.raise_for_status()
    return r.text

def load_scenar( yml_str: str) -> tuple[dict,list]:
    yml = yaml.load(yml_str)

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
        raise RqException("scenario must be a dict or a list", item=yml)
