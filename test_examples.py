import pytest
import glob
import io,os
import sys
import re
from src.reqman4 import main,common
from validate import validate_yaml
from conftest import run_command

def attendings(example_file:str): #THE FUTURE for all tests
    with open(example_file, "r") as f:
        first_line = f.readline().strip()
        second_line = f.readline().strip()
    for line in [first_line,second_line]:
        if line.startswith("#ERROR:"):
            return (False, line[len("#ERROR:"):].strip() ) # ex (False, "Bad ...")
        if line.startswith("#RESULT:"):
            return (True, line[len("#RESULT:"):].strip() ) # ex (True, "4/5")
    return (None,None)        

def simulate(example_file: str,compatibility=0): #THE FUTURE for all tests
    """
    it will run a scenario (yaml file)
    and will check if the result is the one expected
    (in the comment of the file)
    """
    good,info = attendings(example_file)

    args = [example_file]
    if compatibility:
        args.append("-c")
    r = run_command(*args)

    match = re.search(r"(\d+/\d+)", r.output)
    result = match.group(0) if match else None

    if good is True:
        # A "good" file (with #RESULT) should not crash.
        # It can have failing tests (exit_code > 0) or pass (exit_code == 0).
        assert r.exit_code >= 0, f"Expected exit code >= 0 for a #RESULT test, but got {r.exit_code}. Output:\n{r.output}"
        assert result == info, f"Expected result '{info}' but got '{result}'. Output:\n{r.output}"
    elif good is False:
        # A "bad" file (with #ERROR) is expected to fail with a non-zero exit code.
        assert r.exit_code != 0, f"Expected non-zero exit code for an #ERROR test, but got 0. Output:\n{r.output}"
        if info:
            assert info in r.output, f"Expected error message '{info}' not found in output. Output:\n{r.output}"
    else: # good is None
        # A standard file without special tags. Expected to pass completely.
        assert r.exit_code == 0, f"Expected exit code 0 for an OK test, but got {r.exit_code}. Output:\n{r.output}"


def test_no_reqman_conf():
    """ ensure there no reqman.yml, because it will interact with
    scenarios tested in examples folder """
    assert common.guess_reqman_conf([".","examples"]) is None

@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/ok/*.yml")) )
def test_scenarios_ok(example_file):
    assert validate_yaml(example_file,"schema.json")
    simulate(example_file)



@pytest.mark.parametrize("example_file", [i for i in sorted(glob.glob("examples/err/*.yml")) if os.path.basename(i)[0]!="_"] )
def test_scenarios_err(example_file):
    simulate(example_file)


@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/ko/*.yml")) )
def test_scenarios_ko(example_file):
    simulate(example_file)

@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/reqman3/*.yml")) )
def test_scenarios_reqman3(example_file):
    simulate(example_file,1)

# @pytest.mark.skipif(os.getenv("CI") == "true", reason="No internet on CI")
# @pytest.mark.parametrize("example_file", sorted(glob.glob("examples/reals/*.yml")) )
# def test_scenarios_reals(example_file):
#     simulate(example_file)


if __name__ == "__main__":
    ...
    # test_scenarios_reqman3("examples/reqman3/simplest.yml")
    # test_scenarios_err("examples/err/bad_yaml.yml",None)