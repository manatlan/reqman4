import pytest, yaml
from src import scenario

def test_switch():
    conf=yaml.safe_load("""host: http://test

switch:
  env1:
    doc: for dev
    host: http://dev/

  env2:
    doc: for verification
    host: http://verification/

  env3:
    doc: for validation
    host: http://validation/
""")

    t=scenario.Test("examples/test_switch.yml", conf)
    assert list(t.env.switchs.keys()) == [ "env1", "env2", "env3" ]

    with pytest.raises(AssertionError):
      t.apply_switch("unknown")

    assert t.env["host"] == "http://test"

    t.apply_switch("env2")

    assert t.env["host"] == "http://verification/"