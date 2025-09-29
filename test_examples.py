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
    good,info = attendings(example_file)
    print(good,info)
    stdout = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = stdout
    try:
        error=None
        rc = main.reqman(None,[example_file],compatibility=True if compatibility else False)
    except Exception:
        pass
    finally:
        sys.stdout = sys_stdout
    output = stdout.getvalue()
    last_line = output.strip().rsplit('\n', 1)[-1]
    result=re.search( r"(\d+/\d+)",last_line).group(0)

    if good:
        assert rc>=0
        assert result == info
    else:
        assert rc == -1
        assert error
        if info:
            assert info in str(error)


def test_no_reqman_conf():
    """ ensure there no reqman.yml, because it will interact with
    scenarios tested in examples folder """
    assert common.guess_reqman_conf([".","examples"]) is None

@pytest.mark.asyncio
@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/ok/*.yml")) )
async def test_scenarios_ok(example_file):

    assert validate_yaml(example_file,"schema.json")

    et=main.ExecutionTests( [example_file] )
    o = await et.execute()
    assert o.nb_tests_ko == 0



@pytest.mark.parametrize("example_file", [i for i in sorted(glob.glob("examples/err/*.yml")) if os.path.basename(i)[0]!="_"] )
def test_scenarios_err(example_file,capsys):
    #assert not validate_yaml(example_file,"schema.json")
    good,error_message = attendings(example_file)

    result=run_command( example_file )
    assert not good
    assert error_message in result.output


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