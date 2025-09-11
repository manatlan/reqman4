import pytest
from src.reqman4 import main
import respx

@pytest.mark.asyncio
@respx.mock
async def test_standalone_switch(tmp_path):
    # Create a scenario file with its own switch
    scenario_content = """
switch:
    dev:
        root: http://localhost:8080
RUN:
    - GET: /test
      tests:
        - R.status == 200
"""
    scenario_file = tmp_path / "scenario.yml"
    scenario_file.write_text(scenario_content)

    # Mock the HTTP request
    respx.get("http://localhost:8080/test").respond(200, text="OK")

    # Run reqman with the standalone scenario and the dev switch
    r = main.ExcecutionTests([str(scenario_file)], switch="dev")
    o = await r.execute()
    assert o.nb_tests_ko == 0
