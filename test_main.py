from src import main
import pytest


def test_find_scenarios():
    assert list(main.find_scenarios("examples"))

def test_main():
    o1=main.reqman(["examples/classic/test_switch.yml"])
    o2=main.reqman(["examples/single/test_switch.yml"])
    assert o1 is not None
    assert o2 is not None
    assert o1.nb_tests_ko == o2.nb_tests_ko
    
# def test_main_view_only():
#     assert main.reqman(["examples/classic/test_switch.yml"],is_view=True) is None

def test_main_apply_switch():
    o=main.reqman(["examples/classic/test_switch.yml"],"env2")
    assert o is not None
    assert o.nb_tests_ko == 4, "There should be 4 tests ko, because host unreachable"

def test_fnf():
    with pytest.raises(Exception):
        main.reqman(["examples/UNKNOW_FILE.yml"])

def test_switch_apply_unknown():
    # error unknow switch
    with pytest.raises(Exception):
        main.reqman(["examples/classic/test_switch.yml"],"toto")

def test_real():
    o=main.reqman(["examples/real.yml"])
    assert o is not None
    assert o.nb_tests_ko == 1 # 1 failed test, to test

if __name__=="__main__":
    ...