import pytest
import glob
from src import scenario

example_files = glob.glob("examples/*.yml")

@pytest.mark.asyncio
@pytest.mark.parametrize("example_file", example_files)
async def test_scenario_ok(example_file):
    async for i in scenario.test(example_file):
        if i:
            for t, r in i.tests:
                assert r, f"Test failed: {t}"