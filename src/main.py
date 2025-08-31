# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
import os
import sys
import asyncio
import logging
import traceback
import tempfile
import webbrowser
import click
import dotenv; dotenv.load_dotenv()

import config
import scenario
import env
import output

from colorama import init, Fore, Style
from urllib.parse import unquote
logger = logging.getLogger(__name__)
init()

def colorize(color: str, t: str) -> str|None:
    return (color + Style.BRIGHT + str(t) + Fore.RESET + Style.RESET_ALL if t else None)

cy = lambda t: colorize(Fore.YELLOW, t)
cr = lambda t: colorize(Fore.RED, t)
cg = lambda t: colorize(Fore.GREEN, t)
cb = lambda t: colorize(Fore.CYAN, t)
cw = lambda t: colorize(Fore.WHITE, t)


class Output:
    def __init__(self,switch:str|None):
        self.switch = switch
        self.nb_tests=0
        self.nb_tests_ok=0
        self.nb_req=0
        self.htmls=[ output.generate_base() ]

    @property
    def nb_tests_ko(self):
        return self.nb_tests - self.nb_tests_ok

    def begin_scenario(self,file:str):
        print(cb(f"--- RUN {file} ---"))
        self.htmls.append( output.generate_section(file) )

    def write_a_test(self,r:scenario.Result):
        if r:
            self.nb_req+=1
            print(f"{cy(r.request.method)} {unquote(str(r.request.url))} -> {cb(r.response.status_code) if r.response.status_code else cr('X')}")
            for tr in r.tests:
                print(" -",tr.ok and cg("OK") or cr("KO"),":", tr.text)
                self.nb_tests += 1
                if tr.ok:
                    self.nb_tests_ok += 1
            print()
            self.htmls.append( output.generate_request(r) )

    def end_scenario(self):
        pass

    def end_tests(self):
        self.htmls.append( output.generate_final( self.switch, self.nb_tests_ok, self.nb_tests) )

    def open_browser(self):

        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
            f.write("\n".join(self.htmls))
            temp_html_path = f.name

        # Ouvre le fichier HTML dans le navigateur par défaut
        webbrowser.open(f'file://{os.path.abspath(temp_html_path)}')        

async def run_tests(files:list[str], conf:dict|None, switch:str|None=None, show_env:bool=False) -> Output:
    """ Run all tests in files, return number of failed tests """
    output = Output( switch)

    for file in files:
        output.begin_scenario( file )
        try:
            t=scenario.Test(file,conf)
            async for req in t.run(switch):
                output.write_a_test(req)
        except Exception as ex:
            try:
                ex.env = t.env 
            except:
                logger.error(f"Can't get the env on exception {ex}")
                ex.env = None
            raise ex
        
        output.end_scenario( )
        if show_env:
            print(cy("Final environment:"))
            print(env.jzon_dumps(t.env))

    output.end_tests()
    return output

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

def reqman(files:list,switch:str|None=None,vars:dict={},is_view:bool=False,is_debug:bool=False,show_env:bool=False,show_html:bool=False) -> int:
    """New reqman (rq4) prototype"""

    # fix files : extract files (yml/rml) from potentials directories
    files=expand_files(files)

    reqman_conf = config.guess_reqman_conf(files)
    if reqman_conf is None:
        conf = {}
    else:
        print(cy(f"Using {os.path.relpath(reqman_conf)}"))
        conf = config.load_reqman_conf(reqman_conf)
    
    conf.update(vars)

    if is_view:
        for f in files:
            print(cb(f"Analyse {f}"))
            for i in scenario.Scenario(f):
                print(i)
        return 0
    else:
        if is_debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.ERROR)

        try:
            o = asyncio.run(run_tests(files, conf, switch, show_env))
            r = o.nb_tests_ko
            if show_html: o.open_browser()
            if r==0:
                print(cg(f"{o.nb_tests_ok}/{o.nb_tests}"))
            else:
                print(cr(f"{o.nb_tests_ok}/{o.nb_tests}"))
    # except scenario.ScenarException as ex:
        except Exception as ex:
            if is_debug:
                traceback.print_exc()
            if show_env:
                print(cy("Final environment:"))
                print(env.jzon_dumps(ex.env) if hasattr(ex,"env") else "no env")
            print(cr(f"SCENARIO ERROR: {ex}"))
            r = -1

        return r

def guess(args:list):
    ##########################################################################
    #WARNING: it returns only switchs from reqman.conf ! (not from scenario!!!!)
    files = expand_files([i for i in args if os.path.exists(i)])
    if len(files)==1:
        # an unique file
        import yaml
        dico = yaml.safe_load(open(files[0],"r"))
        assert isinstance(dico,dict), f"{files[0]} is not a valid scenario file"
        d=env.Env( **dico )
        if d.switchs:
            print(cy(f"Using switches from {files[0]}"))
            return d.switchs
            
    reqman_conf = config.guess_reqman_conf(files)
    if reqman_conf:
        conf = config.load_reqman_conf(reqman_conf)
        return env.Env(**conf).switchs
    else:
        return {}        
    ##########################################################################

def options_from_files(opt_name:str):
    d=guess(sys.argv[1:] or [])

    ll=[dict( name=k, switch=f"--{k}", help=v.get("doc","???") ) for k,v in d.items()]

    def decorator(f):
        for p in reversed(ll):
            click.option( p['switch'], opt_name, 
                is_flag = True,
                flag_value=p['name'],
                required = False,
                help = p['help'],
            )(f)
        return f
    return decorator


@click.group()
def cli():
    pass

@cli.command()
@click.argument('files', type=click.Path(exists=True,), nargs=-1, required=True)
@options_from_files("switch")
@click.option('-v',"is_view",is_flag=True,default=False,help="Analyze only, do not execute requests")
@click.option('-d',"is_debug",is_flag=True,default=False,help="debug mode")
@click.option('-e',"show_env",is_flag=True,default=False,help="Display final environment")
@click.option('-s',"vars",help="Set variables (ex: -s token=DEADBEAF,id=42)")
@click.option('-i',"is_shebang",is_flag=True,default=False,help="interactif mode (with shebang)")
@click.option('-o',"open_browser",is_flag=True,default=False,help="open result in an html page")
def main(**p):
    """Test an http service with pre-made scenarios, whose are simple yaml files
(More info on https://github.com/manatlan/RQ)"""
    if p["vars"]:
        vars = dict( [ i.split("=",1) for i in p["vars"].split(",") if "=" in i ] )
    else:
        vars = {}

    if p["is_shebang"] and len(p["files"])==1:
        files=p["files"]
        with open(files[0], "r") as f:
            first_line = f.readline().strip()
        if first_line.startswith("#!"): # things like "#!reqman -e -d" should work
            options = first_line.split(" ")[1:]        
            print(cy(f"Use shebang {' '.join(options)}"))
            cmd,*fuck_all_params = sys.argv
            sys.argv=[ cmd, files[0] ] + options
            return main() #redo click parsing !
            
    return reqman(p["files"],p.get("switch",None),vars,p["is_view"],p["is_debug"],p["show_env"],p["open_browser"])

if __name__ == "__main__":
    sys.exit( main() )
