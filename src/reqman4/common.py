# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import os,io,sys
import httpx
from dataclasses import dataclass
import datetime
from . import compat
FIX_SCENAR = compat.fix_scenar

REQMAN_CONF='reqman.yml'

import ruamel.yaml
from ruamel.yaml.comments import CommentedMap as YDict,CommentedSeq as YList
yaml = ruamel.yaml.YAML() # typ=rt
yaml.allow_duplicate_keys = True

def yload(y):
    if isinstance(y,str):
        return yaml.load(y)
    elif isinstance(y,io.TextIOWrapper):
        with y:
            return yaml.load(y)
    else:
        raise Exception("????")
        
class Conf(dict):
    """ Manage Configuration dict, with support for --switch keys """
    def __init__(self, conf:dict):
        self.switchs = {k[2:]:v for k,v in conf.items() if k.startswith("--")}
        assert all(isinstance(v,dict) for k,v in self.switchs.items()), "all switch values must be dict"
        super().__init__({k:v for k,v in conf.items() if not k.startswith("--")})
    def apply(self, *switchs:str) -> "Conf":
        for s in switchs:
            eswitch = self.switchs.get(s)
            if eswitch: self.update( eswitch )
        return self



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
    conf = yload( open(path, 'r') )
    assert_syntax( isinstance(conf, dict) , "reqman.yml must be a mapping")
    return conf

def get_url_content(url:str) -> str:
    r=httpx.get(url)
    r.raise_for_status()
    return r.text




class YScenario:
    def __init__(self, yml:str|io.TextIOWrapper,compatibility:int=0):

        def load_scenar( yml_thing:str|io.TextIOWrapper) -> tuple[YDict,YList]:
            yml = yload(yml_thing)

            if isinstance(yml, YDict):
                # new reqman4 (yml is a dict, and got a RUN section)
                if "RUN" in yml:
                    scenar = yml["RUN"]
                    del yml["RUN"]

                    return (yml,scenar)
                else:
                    return (yml,YList())
            elif isinstance(yml, YList):
                # for simple compat, reqman4 can accept list (but no conf!)
                scenar = yml
                return (YDict(),scenar)
            else:
                raise Exception("scenario must be a dict or a list]")

        if isinstance(yml,io.TextIOWrapper):
            self.filename = yml.name
        else:
            self.filename = "buffer"
        self._conf,self._steps = load_scenar(yml)
        if compatibility>0:
            self._conf,self._steps=FIX_SCENAR(self._conf,self._steps)
            if compatibility>1:
                self.save()



    def save(self): #TODO: continue here
        assert self.filename != "buffer"
        base=self._conf
        base["RUN"] = self._steps
        base.yaml_set_start_comment(f"Converted from {self.filename} {datetime.datetime.now()}")
        yaml.indent(mapping=2, sequence=2, offset=0)
        # shutil.copy2(self.filename,self.filename)
        new_file=self.filename+".new.yml"
        with open(new_file,"w+") as fid:
            yaml.dump(base, fid)
        print("CREATE NEW REQMAN4 FILE:",new_file)

    def __str__(self):
        return f"YScenario '{self.filename}'\n* DICT:{self._conf}\n* LIST:{self._steps}"

# if __name__=="__main__":
#     yaml_file="examples/works_on/old.yml"
#     ys=YScenario( open(yaml_file,"r") )
#     # ys.save()    
#     print(ys)

