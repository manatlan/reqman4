import pytest,os
import glob,io,sys,re
from src.reqman4 import scenario,main,common
from validate import validate_yaml


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

def simulate(example_file: str): #THE FUTURE for all tests
    stdout = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = stdout
    error = None
    rc = 0
    try:
        rc = main.reqman([example_file])
    except Exception as e:
        error = e
        rc = -1
    output = stdout.getvalue()
    sys.stdout = sys_stdout
    return rc, output, error

# @pytest.mark.parametrize("example_file", sorted(glob.glob("examples/ko/*.yml")) )
# def test_examples_ko(example_file):
#     rc, output, error = simulate(example_file)
#     good,info = attendings(example_file)
#     assert good
#     assert rc > 0
#     last_line = output.strip().rsplit('\n', 1)[-1]
#     result=re.search( r"(\d+/\d+)",last_line).group(0)
#     assert result == info

# @pytest.mark.parametrize("example_file", sorted(glob.glob("examples/reqman3/*.yml")) )
# def test_examples_compat(example_file):
#     rc, output, error = simulate(example_file)
#     good,info = attendings(example_file)
#     assert good
#     assert rc == 0
#     last_line = output.strip().rsplit('\n', 1)[-1]
#     result=re.search( r"(\d+/\d+)",last_line).group(0)
#     assert result == info

# @pytest.mark.skipif(os.getenv("CI") == "true", reason="No internet on CI")
# @pytest.mark.parametrize("example_file", sorted(glob.glob("examples/reals/*.yml")) )
# def test_examples_reals(example_file):
#     rc, output, error = simulate(example_file)
#     good,info = attendings(example_file)

#     if good:
#         assert rc >= 0
#         if info:
#             last_line = output.strip().rsplit('\n', 1)[-1]
#             result=re.search( r"(\d+/\d+)",last_line).group(0)
#             assert result == info
#     else:
#         assert rc == -1
#         if info:
#             assert info in output or info in str(error)


def test_no_reqman_conf():
    """ ensure there no reqman.conf, because it will interact with
    scenarios tested in examples folder """
    assert common.guess_reqman_conf([".","examples"]) is None

@pytest.mark.asyncio
@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/ok/*.yml")) )
async def test_examples_ok(example_file):

    assert validate_yaml(example_file,"schema.json")

    s=scenario.Scenario(example_file)
    print(s) # test repr
    for step in s:
        print(step) # test step.__repr__
    async for echange in s.execute():
        if echange:
            for tr in echange.tests:
                assert tr.ok, f"Test failed: {tr.text}"


@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/err/*.yml")) )
def test_examples_err(example_file):
    rc, output, error = simulate(example_file)
    good,error_message = attendings(example_file)
    assert not good
    assert rc == -1
    if error_message:
        assert error_message in output or error_message in str(error)

@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/ko/*.yml")) )
def test_examples_ko(example_file):
    simulate(example_file)

@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/reqman3/*.yml")) )
def test_examples_compat(example_file):
    simulate(example_file)

@pytest.mark.skipif(os.getenv("CI") == "true", reason="No internet on CI")
@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/reals/*.yml")) )
def test_examples_reals(example_file):
    simulate(example_file)


if __name__ == "__main__":
    ...