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
import json

import click
import dotenv; dotenv.load_dotenv()

import config
import scenario
import env

from colorama import init, Fore, Style

init()

def colorize(color: str, t: str) -> str|None:
    return (color + Style.BRIGHT + str(t) + Fore.RESET + Style.RESET_ALL if t else None)

cy = lambda t: colorize(Fore.YELLOW, t)
cr = lambda t: colorize(Fore.RED, t)
cg = lambda t: colorize(Fore.GREEN, t)
cb = lambda t: colorize(Fore.CYAN, t)
cw = lambda t: colorize(Fore.WHITE, t)


async def run_tests(files:list[str], conf:dict|None, show_env:bool) -> int:
    """ Run all tests in files, return number of failed tests """
    ll=[]
    nb_tests_failed=0
    for file in files:
        print(cb(f"--- RUN {file} ---"))
        t=scenario.Test(file,conf)
        async for i in t.run():
            if i:
                print(f"{cy(i.request.method)} {i.request.url} -> {cb(i.response.status_code)}")
                for test,ok in i.tests:
                    if not ok:
                        nb_tests_failed += 1
                    print(" -",ok and cg("OK") or cr("KO"),":", test)
                print()
        if show_env:
            print(cy("Final environment:"))
            print(env.jzon_dumps(t.env))

    return nb_tests_failed

def find_scenarios(path_folder: str, filters=(".yml", ".rml")):
    for folder, subs, files in os.walk(path_folder):
        if (folder in [".", ".."]) or ( not os.path.basename(folder).startswith((".", "_"))):
            for filename in files:
                if filename.lower().endswith(
                    filters
                ) and not filename.startswith((".", "_")):
                    yield os.path.join(folder, filename)

def reqman(files:list,is_view:bool=False,is_debug:bool=False,show_env:bool=False) -> int:
    """New reqman (rq4) prototype"""

    # fix files : extract files (yml/rml) from potentials directories
    ll=[]
    for i in files:
        if os.path.isdir(i):
            ll.extend( list(find_scenarios(i)) )
        else:
            ll.append(i)
    files = ll

    reqman_conf = config.guess_reqman_conf(files)
    if reqman_conf is None:
        print(cy("No reqman.conf found"))
        conf = None
    else:
        print(cy(f"Using reqman.conf: {os.path.relpath(reqman_conf)}"))
        conf = config.load_reqman_conf(reqman_conf)

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

        r = asyncio.run(run_tests(files, conf, show_env))

        return r


@click.command()
@click.argument('files', type=click.Path(exists=True,), nargs=-1, required=True)
@click.option('-v',"--view","is_view",is_flag=True,default=False,help="Analyze only, do not execute requests")
@click.option('-d',"--debug","is_debug",is_flag=True,default=False,help="debug mode")
@click.option('-e',"--env","show_env",is_flag=True,default=False,help="Display final environment")
def command(files:list,is_view:bool,is_debug:bool,show_env:bool) -> int:
    return reqman(files,is_view,is_debug,show_env)

def main():
    try:
        sys.exit( command() )
    except KeyboardInterrupt:
        sys.exit(0)
    except scenario.ScenarException as ex:
        print(cr(f"SCENARIO ERROR: {ex}"))
        sys.exit(-1)

if __name__ == "__main__":
    main()