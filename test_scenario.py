import pytest
import glob
from src import scenario,main

@pytest.mark.asyncio
@pytest.mark.parametrize("example_file", glob.glob("examples/ok/*.yml") )
async def test_scenarios_ok(example_file):
    s=scenario.Scenario(example_file)
    print(s) # test repr
    for step in s:
        print(step) # test step.__repr__
    async for echange in s.execute():
        if echange:
            for tr in echange.tests:
                assert tr.ok, f"Test failed: {tr.text}"


@pytest.mark.asyncio
@pytest.mark.parametrize("example_file", glob.glob("examples/err/*.yml") )
async def test_scenarios_err(example_file):
    with open(example_file, "r") as f:
        first_line = f.readline().strip()
    assert first_line.startswith("#ERROR:")
    error_message = first_line[len("#ERROR:"):].strip()

    with pytest.raises(scenario.ScenarException) as excinfo:
        s=scenario.Scenario(example_file)
        async for echange in s.execute():
            ...
    assert error_message in str(excinfo.value)

@pytest.mark.parametrize("example_file", glob.glob("examples/ko/*.yml") )
def test_scenarios_ko(example_file):
    with open(example_file, "r") as f:
        first_line = f.readline().strip()
    assert first_line.startswith("#KO:")
    nb_ko = int(first_line[len("#KO:"):].strip())

    assert main.reqman([example_file]) == nb_ko
