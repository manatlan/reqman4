
import subprocess
import sys

def test_main_entrypoint():
    """Test the __main__.py entrypoint."""
    scenario_path = "examples/ok/simple.yml"
    result = subprocess.run(
        [sys.executable, "-m", "src.reqman4", scenario_path],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--- RUN examples/ok/simple.yml ---" in result.stdout
    assert "8/8" in result.stdout

if __name__ == "__main__":
    test_main_entrypoint()