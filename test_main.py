from src.reqman4 import main
import pytest,os


def test_find_scenarios():
    assert list(main.find_scenarios("examples"))

def test_main_apply_switch():
    assert main.reqman(["examples/classic/test_switch.yml"],"env2") == -1, "There should be a scenario error, because host unreachable"

def test_fnf():
    assert main.reqman(["examples/UNKNOW_FILE.yml"]) == -1

def test_switch_apply_unknown():
    # error unknow switch
    assert main.reqman(["examples/classic/test_switch.yml"],"toto") == -1

@pytest.mark.skipif(os.getenv("CI") == "true", reason="No internet on CI")
def test_the_scenario_example():
    assert main.reqman(["scenario.yml"]) == -1

if __name__=="__main__":
    ...