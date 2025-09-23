from src.reqman4 import main,common
import pytest,os


def test_find_scenarios():
    assert list(common.find_scenarios("examples"))

def test_main_apply_switch():
    assert main.reqman(None,["examples/classic/test_switch.yml"],switch="env2") == 4, "There should be 4 tests ko, because host unreachable"

def test_fnf():
    assert main.reqman(None,["examples/UNKNOW_FILE.yml"]) == 0

# def test_switch_apply_unknown():
#     # error unknow switch
#     with pytest.raises(Exception):
#         main.reqman(["examples/classic/test_switch.yml"],"toto")

# @pytest.mark.skipif(os.getenv("CI") == "true", reason="No internet on CI")
# def test_the_scenario_example():
#     assert main.reqman(["scenario.yml"]) == 0 

if __name__=="__main__":
    ...