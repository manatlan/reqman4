from src.reqman4 import main,common
import pytest


def test_find_scenarios():
    assert list(common.find_scenarios("examples"))

def test_main_apply_switch_defaulting():
    assert main.reqman(None,["examples/classic/test_switch.yml"]) == 0, "test is kaputt ?!"

def test_main_apply_real_switch():
    assert main.reqman(None,["examples/classic/test_switch.yml"],switchs=["env2"]) > 0, "There should be errors (get/begin)"

def test_fnf():
    assert main.reqman(None,["examples/UNKNOW_FILE.yml"]) == 0

def test_switch_apply_unknown():
    assert main.reqman(None,["examples/classic/test_switch.yml"],switchs=["toto"]) == -1

# @pytest.mark.skipif(os.getenv("CI") == "true", reason="No internet on CI")
# def test_the_scenario_example():
#     assert main.reqman(["scenario.yml"]) == 0 

if __name__=="__main__":
    ...