from src.reqman4 import main,common
import pytest
import subprocess
import sys

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

def test_cli_no_files():
    # Execute the CLI tool as a subprocess without arguments
    result = subprocess.run([sys.executable, "-m", "src.reqman4"], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Missing argument 'FILES...'" in result.stderr

def test_cli_unknown_file():
    # Execute the CLI tool as a subprocess with a non-existent file
    result = subprocess.run([sys.executable, "-m", "src.reqman4", "examples/UNKNOW_FILE.yml"], capture_output=True, text=True)
    assert result.returncode != 0
    assert "File not found 'examples/UNKNOW_FILE.yml'" in result.stderr

if __name__=="__main__":
    ...