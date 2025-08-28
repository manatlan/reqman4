from src import main
import pytest

def test_find_scenarios():
    assert list(main.find_scenarios("examples"))

def test_main():
    assert main.reqman(["examples/test_switch.yml"]) == 0

def test_main_view_only():
    assert main.reqman(["examples/test_switch.yml"],is_view=True) == 0

def test_fnf():
    with pytest.raises(main.scenario.ScenarException):
        main.reqman(["examples/UNKNOW_FILE.yml"])

