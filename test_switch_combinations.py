import pytest
from src.reqman4 import main
import respx
import os
import shutil

@pytest.fixture
def setup_test_env(tmp_path):
    # Create classic folder
    classic_path = tmp_path / "classic"
    classic_path.mkdir()
    (classic_path / "reqman.conf").write_text("""
switch:
    env1:
        root: http://classic-env1
    env2:
        root: http://classic-env2
BEGIN:
    - GET: /begin
      tests:
        - R.status == 200
END:
    - GET: /end
      tests:
        - R.status == 200
""")
    (classic_path / "scenario.yml").write_text("""
RUN:
    - GET: /test
      tests:
        - R.status == 200
""")

    # Create mixed folder
    mixed_path = tmp_path / "mixed"
    mixed_path.mkdir()
    (mixed_path / "reqman.conf").write_text("""
switch:
    env1:
        root: http://mixed-env1
    env2:
        root: http://mixed-env2
""")
    (mixed_path / "scenario.yml").write_text("""
BEGIN:
    - GET: /begin
      tests:
        - R.status == 200
END:
    - GET: /end
      tests:
        - R.status == 200
RUN:
    - GET: /test
      tests:
        - R.status == 200
""")

    # Create single folder
    single_path = tmp_path / "single"
    single_path.mkdir()
    (single_path / "scenario.yml").write_text("""
switch:
    env1:
        root: http://single-env1
    env2:
        root: http://single-env2
BEGIN:
    - GET: /begin
      tests:
        - R.status == 200
END:
    - GET: /end
      tests:
        - R.status == 200
RUN:
    - GET: /test
      tests:
        - R.status == 200
""")

    yield tmp_path

    # Teardown
    shutil.rmtree(classic_path)
    shutil.rmtree(mixed_path)
    shutil.rmtree(single_path)

@pytest.mark.asyncio
@respx.mock
async def test_switch_combinations(setup_test_env):
    tmp_path = setup_test_env

    # Classic case
    respx.get("http://classic-env2/begin").respond(200)
    respx.get("http://classic-env2/test").respond(200)
    respx.get("http://classic-env2/end").respond(200)

    classic_scenario = tmp_path / "classic" / "scenario.yml"
    os.chdir(tmp_path / "classic")
    r = main.ExecutionTests([str(classic_scenario)], switch="env2")
    o = await r.execute()
    assert o.nb_tests_ko == 0

    # Mixed case
    respx.get("http://mixed-env2/begin").respond(200)
    respx.get("http://mixed-env2/test").respond(200)
    respx.get("http://mixed-env2/end").respond(200)

    mixed_scenario = tmp_path / "mixed" / "scenario.yml"
    os.chdir(tmp_path / "mixed")
    r = main.ExecutionTests([str(mixed_scenario)], switch="env2")
    o = await r.execute()
    assert o.nb_tests_ko == 0

    # Single case
    respx.get("http://single-env2/begin").respond(200)
    respx.get("http://single-env2/test").respond(200)
    respx.get("http://single-env2/end").respond(200)

    single_scenario = tmp_path / "single" / "scenario.yml"
    os.chdir(tmp_path / "single")
    r = main.ExecutionTests([str(single_scenario)], switch="env2")
    o = await r.execute()
    assert o.nb_tests_ko == 0
