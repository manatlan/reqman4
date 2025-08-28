import pytest
import glob
from src import scenario

@pytest.mark.asyncio
@pytest.mark.parametrize("example_file", glob.glob("examples/ok/*.yml") )
async def test_scenarios_ok(example_file):
    s=scenario.Test(example_file)
    print(s.scenario) # test repr
    for step in s.scenario:
        print(step) # test step.__repr__
    async for echange in s.run():
        if echange:
            for test, ok in echange.tests:
                assert ok, f"Test failed: {test}"


@pytest.mark.asyncio
@pytest.mark.parametrize("example_file", glob.glob("examples/ko/*.yml") )
async def test_scenarios_ko(example_file):
    with open(example_file, "r") as f:
        first_line = f.readline().strip()
    assert first_line.startswith("#ERROR:")
    error_message = first_line[len("#ERROR:"):].strip()

    with pytest.raises(scenario.ScenarException) as excinfo:
        s=scenario.Test(example_file)
        async for echange in s.run():
            pass
    assert error_message in str(excinfo.value)
