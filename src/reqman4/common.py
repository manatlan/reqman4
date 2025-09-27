# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import os
import io
import httpx
from dataclasses import dataclass
import datetime
from . import compat
FIX_SCENAR = compat.fix_scenar

REQMAN_CONF='reqman.yml'

import ruamel.yaml
from ruamel.yaml.comments import CommentedMap as YDict,CommentedSeq as YList



class BytesUtf8(bytes):
    """A bytes subclass that normalizes input strings/bytes to UTF-8 encoding.
    it stores the original encoding used for input in the 'encoding' attribute.
    """
    LATIN = "cp1252" # Windows Western Europe
    UTF8 = "utf8"

    encoding: str  # "utf8" or "latin_1"

    def __new__(cls, x: str | bytes):
        # Returns an instance of bytes (immutable) after normalization + approximate encoding detection.
        if isinstance(x, str):
            # Heuristic: detect UTF-8 mojibake decoded as latin-1 (presence of typical Ã, Â characters).
            try:
                candidate = x.encode(BytesUtf8.LATIN)
            except UnicodeEncodeError:
                # Character not representable in latin-1: consider the source as already correct UTF-8.
                value = x.encode(BytesUtf8.UTF8)
                enc = BytesUtf8.UTF8
            else:
                if any(ch in x for ch in ('Ã', 'Â')):
                    value = candidate  # bytes assumed to be the original UTF-8 incorrectly decoded before
                    enc = BytesUtf8.LATIN
                else:
                    value = x.encode(BytesUtf8.UTF8)
                    enc = BytesUtf8.UTF8
        elif isinstance(x, bytes):
            # Try UTF-8, otherwise assume latin-1 and re-encode in UTF-8 for uniformity.
            try:
                x.decode(BytesUtf8.UTF8)
                value = x
                enc = BytesUtf8.UTF8
            except UnicodeDecodeError:
                value = x.decode(BytesUtf8.LATIN).encode(BytesUtf8.UTF8)
                enc = BytesUtf8.LATIN
        else:
            raise TypeError(type(x))
        obj = super().__new__(cls, value)
        obj.encoding = enc
        return obj

class YamlObject(ruamel.yaml.YAML):
    def __init__(self):
        ruamel.yaml.YAML.__init__(self)
        self.default_flow_style = False
        self.block_seq_indent = 2
        self.indent = 4
        self.allow_unicode = True
        self.allow_duplicate_keys = True        
        self.encoding = 'utf-8'

def yload(y) -> YDict|YList:
    if isinstance(y,str) or isinstance(y,bytes):
        b=BytesUtf8(y)
        yml = YamlObject().load(b)
        yml._encoding = b.encoding
        return yml
    elif isinstance(y,io.TextIOWrapper) or isinstance(y,io.BufferedReader):
        with y:
            b=BytesUtf8(y.read())
            yml= YamlObject().load(b)
            yml._encoding = b.encoding
            return yml
    else:
        raise Exception(f"yload error {y=}")
        
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


def find_scenarios(path_folder: str, filters=(".yml",)):
    for folder, subs, files in os.walk(path_folder):
        if (folder in [".", ".."]) or ( not os.path.basename(folder).startswith((".", "_"))):
            for filename in files:
                if filename.lower().endswith(filters) and not filename.startswith((".", "_")) and filename != REQMAN_CONF:
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
    def __init__(self, yml:str|io.TextIOWrapper|io.BufferedReader,compatibility:int=0):
        self.encoding ="utf-8"

        def load_scenar( yml_thing:str|io.TextIOWrapper|io.BufferedReader) -> tuple[YDict,YList]:
            yml = yload(yml_thing)
            self.encoding = yml._encoding

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
        self.conf = Conf( self._conf )

    def save(self) -> bytes|None: #TODO: continue here
        
        base=self._conf
        base["RUN"] = self._steps
        base.yaml_set_start_comment(f"Converted from {self.filename} {datetime.datetime.now()}")

        yaml=YamlObject()
        yaml.width = 200
        yaml.indent(mapping=2, sequence=2, offset=0)
        yaml.encoding = self.encoding
        # shutil.copy2(self.filename,self.filename)

        if self.filename != "buffer":
            new_file=self.filename+".new.yml"
            with open(new_file,"wb+") as fid:
                yaml.dump(base, fid)
            print("CREATE NEW REQMAN4 FILE:",new_file)
        else:
            f = io.BytesIO()
            yaml.dump(base, f)
            f.seek(0)
            return f.read()

    def __str__(self):
        return f"YScenario '{self.filename}' ({self.encoding})\n* DICT:{self._conf}\n* LIST:{self._steps}"

if __name__=="__main__":
    ...