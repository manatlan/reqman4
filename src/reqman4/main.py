# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import os
import sys
import asyncio
import logging
import traceback
import tempfile
import webbrowser
import click
from colorama import init, Fore, Style
from urllib.parse import unquote
import dotenv; dotenv.load_dotenv()

# reqman imports
from . import __version__ as VERSION
from . import common
from . import scenario
from . import env
from . import output

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

    def write_a_test(self,r:common.Result):
        if r:
            self.nb_req+=1
            print(f"{cy(r.request.method)} {unquote(str(r.request.url))} -> {cb(r.response.status_code) if r.response.status_code else cr('X')}")
            for tr in r.tests:
                color = {True:cg,False:cr,None:cr}[tr.ok]
                print(" -",color(str(tr)),":", tr.text)
                self.nb_tests += 1
                if tr.ok:
                    self.nb_tests_ok += 1
            print()
            self.htmls.append( output.generate_request(r) )

    def end_scenario(self):
        pass

    def end_tests(self):
        self.htmls.append( output.generate_final( self.switch, self.nb_tests_ok, self.nb_tests) )

        r = self.nb_tests_ko
        if r==0:
            print(cg(f"{self.nb_tests_ok}/{self.nb_tests}"))
        else:
            print(cr(f"{self.nb_tests_ok}/{self.nb_tests}"))


    def open_browser(self):

        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding="utf-8") as f:
            f.write("\n".join(self.htmls))
            temp_html_path = f.name

        # Ouvre le fichier HTML dans le navigateur par défaut
        webbrowser.open(f'file://{os.path.abspath(temp_html_path)}')        

class ReqmanException(Exception):
    env: env.Env|None

def display_env( x ):
    print(cy("Final environment:"))
    print(x if x is not None else "no env")



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

class ExcecutionTests:
    def __init__(self,files:list,switch:str|None=None,vars:dict={}):
        # fix files : extract files (yml/rml) from potentials directories
        self.files=expand_files(files)
        
        # init the conf
        reqman_conf = common.guess_reqman_conf(self.files)
        if reqman_conf is None:
            conf = {}
        else:
            print(cy(f"Using {os.path.relpath(reqman_conf)}"))
            conf = common.load_reqman_conf(reqman_conf)

        # update with vars from command line
        conf.update(vars)

        self.env = env.Env( **conf )

        # apply the switch
        if switch:
            # First, load all scenarios to get all possible switches
            for file in self.files:
                # just load to get switches in self.env
                scenario.Scenario(file, self.env)

            common.assert_syntax(switch in self.env.switchs.keys(), f"Unknown switch '{switch}'")
            self.env.update( self.env.switchs[switch] )
        self._switch = switch


    def view(self):
        for f in self.files:
            print(cb(f"Analyse {f}"))
            s=scenario.Scenario(f, self.env)

            if "BEGIN" in self.env:
                print("BEGIN", scenario.StepCall(s, {scenario.OP.CALL:"BEGIN"}) )

            for i in s:
                print(i)

            if "END" in self.env:
                print("END", scenario.StepCall(s, {scenario.OP.CALL:"END"}) )

    async def execute(self) -> Output:
        """ Run all tests in files, return number of failed tests """
        output = Output(self._switch)

        for file in self.files:
            output.begin_scenario(file)

            try:
                scenar = scenario.Scenario(file, self.env)
                async for req in scenar.execute(with_begin=(file == self.files[0]), with_end=(file == self.files[-1])):
                    output.write_a_test(req)
                self.env = scenar.env  # needed !
            except common.RqException as ex:
                ex = ReqmanException(ex)
                try:
                    ex.env = scenar.env
                except:
                    logger.error(f"Can't get the env on exception {ex}")
                    ex.env = None
                raise ex

            output.end_scenario()

        output.end_tests()
        return output




def guess(args:list):
    ##########################################################################
    files = expand_files([i for i in args if os.path.exists(i)])
    reqman_conf = common.guess_reqman_conf(files)
    if reqman_conf:
        conf = common.load_reqman_conf(reqman_conf)
    else:
        conf = {}

    if len(files)==1:
        # an unique file
        s = scenario.Scenario(files[0],env.Env(**conf))
        if s.env.switchs:
            print(cy(f"Using switches from {files[0]}"))
        return s.env.switchs
    else:
        return env.Env(**conf).switchs
    ##########################################################################

def options_from_files(opt_name:str):
    try:
        d=guess(sys.argv[1:] or [])
    except common.RqException as ex:
        print(cr(f"START ERROR: {ex}"))
        sys.exit(-1)

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


def patch_docstring(f):
    f.__doc__+= f" (version:{VERSION})"
    return f

@cli.command()
@click.argument('files', nargs=-1, required=True ) #help="Scenarios yml/rml (local or http)"
# @click.argument('files', type=click.Path(exists=True,), nargs=-1, required=True)
@options_from_files("switch")
@click.option('-v',"is_view",is_flag=True,default=False,help="Analyze only, do not execute requests")
@click.option('-d',"is_debug",is_flag=True,default=False,help="debug mode")
@click.option('-e',"show_env",is_flag=True,default=False,help="Display final environment")
@click.option('-s',"vars",help="Set variables (ex: -s token=DEADBEAF,id=42)")
@click.option('-i',"is_shebang",is_flag=True,default=False,help="interactif mode (with shebang)")
@click.option('-o',"open_browser",is_flag=True,default=False,help="open result in an html page")
@patch_docstring
def command(**p) -> int:
    """Test an http service with pre-made scenarios, whose are simple yaml files
(More info on https://github.com/manatlan/reqman4) """
    return reqman(**p)

def reqman(files:list,switch:str|None=None,vars:str="",show_env:bool=False,is_debug:bool=False,is_view:bool=False,is_shebang:bool=False,open_browser:bool=False) -> int:
    if vars:
        dvars = dict( [ i.split("=",1) for i in vars.split(",") if "=" in i ] )
    else:
        dvars = {}

    if is_shebang and len(files)==1:

        with open(files[0], "r") as f:
            first_line = f.readline().strip()
        if first_line.startswith("#!"): # things like "#!reqman -e -d" should work
            options = first_line.split(" ")[1:]        
            print(cy(f"Use shebang {' '.join(options)}"))
            cmd,*fuck_all_params = sys.argv
            sys.argv=[ cmd, files[0] ] + options
            return command() #redo click parsing !


    if is_debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    try:
        r = ExcecutionTests( files,switch,dvars)
        if is_view:
            r.view()
            return 0
        else:
            o = asyncio.run(r.execute())

            if show_env:
                display_env(r.env)

            if open_browser:
                o.open_browser()

            return o.nb_tests_ko

    except ReqmanException as ex:
        if is_debug:
            traceback.print_exc()
        if show_env:
            display_env( ex.env if hasattr(ex,"env") else None)
        print(cr(f"SCENARIO ERROR: {ex}"))
        return -1


    
