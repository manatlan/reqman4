import pytest, yaml
from src import scenario

def test_switch():
    conf=yaml.safe_load("""root: http://test

switch:
  env1:
    doc: for dev
    root: http://dev/

  env2:
    doc: for verification
    root: http://verification/

  env3:
    doc: for validation
    root: http://validation/
""")

    t=scenario.Test("examples/classic/test_switch.yml", conf)
    assert list(t.env.switchs.keys()) == [ "env1", "env2", "env3" ]

    with pytest.raises(AssertionError):
      t.apply_switch("unknown")

    assert t.env["root"] == "http://test"

    t.apply_switch("env2")

    assert t.env["root"] == "http://verification/"