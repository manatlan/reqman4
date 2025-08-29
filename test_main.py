from src import main
import pytest


def test_find_scenarios():
    assert list(main.find_scenarios("examples"))

def test_main():
    assert main.reqman(["examples/classic/test_switch.yml"]) == 0

def test_main_view_only():
    assert main.reqman(["examples/classic/test_switch.yml"],is_view=True) == 0

def test_main_apply_switch():
    #tests ko, car host unreachable
    assert main.reqman(["examples/classic/test_switch.yml"],"env2") == 1

def test_fnf():
    assert main.reqman(["examples/UNKNOW_FILE.yml"])==-1

def test_switch_apply_unknown():
    # error unknow switch
    assert main.reqman(["examples/classic/test_switch.yml"],"toto") == -1

if __name__=="__main__":
    main.reqman(["examples/classic/test_switch.yml"],"toto")