# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/RQ
# #############################################################################
import click
import sys
import asyncio
import logging

import pycode
import env
import config
import scenario
import request
import dotenv; dotenv.load_dotenv()

from colorama import init, Fore, Style

init()

def colorize(color: str, t: str) -> str|None:
    return (color + Style.BRIGHT + str(t) + Fore.RESET + Style.RESET_ALL if t else None)

cy = lambda t: colorize(Fore.YELLOW, t)
cr = lambda t: colorize(Fore.RED, t)
cg = lambda t: colorize(Fore.GREEN, t)
cb = lambda t: colorize(Fore.CYAN, t)
cw = lambda t: colorize(Fore.WHITE, t)


async def run_tests(files:list[str]) -> int:
    ll=[]
    for file in files:
        print(cb(f"--- RUN {file} ---"))
        async for i in scenario.test(file):
            if i:
                print(f"{cy(i.request.method)} {i.request.url} -> {cb(i.response.status_code)}")
                for t,r in i.tests:
                    print(" -",r and cg("OK") or cr("KO"),":", t)
                print()

    return 0

@click.command()
@click.argument('files', type=click.Path(exists=True,), nargs=-1, required=True)
@click.option('-v',"--view","is_view",is_flag=True,default=False,help="Analyze only, do not execute requests")
@click.option('-d',"--debug","is_debug",is_flag=True,default=False,help="debug mode")
def command(files:list,is_view:bool,is_debug:bool) -> int:
    """Simple program that greets NAME for a total of COUNT times."""
    reqman_conf = config.guess_reqman_conf(files)
    if reqman_conf is None:
        print(cr("No reqman.conf found"))
    else:
        print(f"Using reqman.conf: {reqman_conf}")
        conf = config.load_reqman_conf(reqman_conf)
        print(conf)

    if is_view:
        for f in files:
            print(cb(f"Analyse {f}"))
            for i in scenario.Scenario(f):
                print(i)
        return 0
    else:

        if is_debug:
            pycode.logger.setLevel(logging.DEBUG)
            request.logger.setLevel(logging.DEBUG)
            env.logger.setLevel(logging.DEBUG)
            scenario.logger.setLevel(logging.DEBUG)
        else:
            pycode.logger.setLevel(logging.ERROR)
            request.logger.setLevel(logging.ERROR)
            env.logger.setLevel(logging.ERROR)
            scenario.logger.setLevel(logging.ERROR)

        asyncio.run(run_tests(files))
        return 0

def main():
    try:
        x=command()
    except Exception as e:
        print(cr(f"FATAL ERROR: {e}"))
        x=-1
    sys.exit(x)

if __name__ == "__main__":
    main()