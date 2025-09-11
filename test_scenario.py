import pytest,os
import glob
from src.reqman4 import scenario,main,common
from validate import validate_yaml


def attendings(example_file:str): #THE FUTURE
    with open(example_file, "r") as f:
        first_line = f.readline().strip()
        second_line = f.readline().strip()
    for line in [first_line,second_line]:
        if line.startswith("#ERROR:"):
            return (False, line[len("#ERROR:"):].strip() ) # ex (False, "Bad ...")
        if line.startswith("#RESULT:"):
            return (True, line[len("#RESULT:"):].strip() ) # ex (True, "4/5")
    return (None,None)        


def test_no_reqman_conf():
    """ ensure there no reqman.conf, because it will interact with
    scenarios tested in examples folder """
    assert common.guess_reqman_conf([".","examples"]) is None

@pytest.mark.asyncio
@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/ok/*.yml")) )
async def test_scenarios_ok(example_file):

    if "compat" not in example_file:
        assert validate_yaml(example_file,"schema.json")


    s=scenario.Scenario(example_file)
    print(s) # test repr
    for step in s:
        print(step) # test step.__repr__
    async for echange in s.execute():
        if echange:
            for tr in echange.tests:
                assert tr.ok, f"Test failed: {tr.text}"


@pytest.mark.asyncio
@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/err/*.yml")) )
async def test_scenarios_err(example_file):

    #assert not validate_yaml(example_file,"schema.json")

    with open(example_file, "r") as f:
        first_line = f.readline().strip()
    assert first_line.startswith("#ERROR:")
    error_message = first_line[len("#ERROR:"):].strip()

    with pytest.raises(Exception) as excinfo:
        s=scenario.Scenario(example_file)
        async for echange in s.execute():
            ...
    assert error_message in str(excinfo.value)

@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/ko/*.yml")) )
def test_scenarios_ko(example_file):
    with open(example_file, "r") as f:
        first_line = f.readline().strip()
    assert first_line.startswith("#KO:")
    nb_ko = int(first_line[len("#KO:"):].strip())

    rc=main.reqman([example_file])
    assert rc == nb_ko


@pytest.mark.skipif(os.getenv("CI") == "true", reason="No internet on CI")
@pytest.mark.parametrize("example_file", sorted(glob.glob("examples/reals/*.yml")) )
def test_scenarios_reals(example_file):
    test_scenarios_ko(example_file)
