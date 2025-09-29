import sys
import os
from click.testing import CliRunner
from src.reqman4 import main

def run_command(*args):
    original_argv = sys.argv
    try:
        sys.argv = ['reqman4'] + list(args)
        # if 'src.reqman4.main' in sys.modules:
        #     del sys.modules['src.reqman4.main']
        import importlib
        importlib.reload(main)

        # 
        runner = CliRunner()
        result = runner.invoke(main.command, list(args))
    finally:
        sys.argv = original_argv
    return result

def pytest_sessionstart(session):
    os.environ["USER"]="me"