# -*- coding: utf-8 -*-
import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from src.reqman4 import main,common

@pytest.fixture
def simple_scenario():
    return "examples/ok/simple.yml"

@pytest.fixture
def switch_scenario():
    return "examples/classic/test_switch.yml"

# def test_reqman_view_mode(simple_scenario, capsys):
#     """Test reqman in view mode (-v)."""
#     assert main.reqman(None,[simple_scenario], is_view=True) == 0
#     captured = capsys.readouterr()
#     assert "Analyse examples/ok/simple.yml" in captured.out
#     assert "Step GET:/test?json={{ toto }}" in captured.out

def test_reqman_show_env(simple_scenario, capsys):
    """Test reqman with show environment flag (-e)."""
    assert main.reqman(None,[simple_scenario], show_env=True) == 0 # respx mock will make it pass
    captured = capsys.readouterr()
    assert "Final environment:" in captured.out
    assert '"root": "http://test"' in captured.out

@patch('src.reqman4.main.webbrowser.open')
def test_reqman_open_browser(mock_open, simple_scenario):
    """Test reqman with open browser flag (-o)."""
    assert main.reqman(None,[simple_scenario], open_browser=True) == 0 # respx mock will make it pass
    mock_open.assert_called_once()
    # Check that the call was with a file path
    assert mock_open.call_args[0][0].startswith('file://')

def test_reqman_shebang(tmp_path, capsys):
    """Test reqman with shebang support (-i)."""
    p_ok = tmp_path / "ok.yml"
    p_ok.write_text("#!reqman -s host=http://localhost:8000\n"
                    "run: http://{host}/get\n"
                    "tests: [200]")

    original_argv = sys.argv
    sys.argv = ['reqman', str(p_ok), '-i']
    try:
        with patch('src.reqman4.main.command') as mock_cmd:
            main.reqman(None,files=[str(p_ok)], is_shebang=True)
            assert sys.argv[1:] == [str(p_ok), '-s', 'host=http://localhost:8000']
            mock_cmd.assert_called_once()
    finally:
        sys.argv = original_argv

def test_expand_files(tmp_path):
    """Test directory expansion to find scenario files."""
    d = tmp_path / "scenarios"
    d.mkdir()
    f1 = d / "test1.yml"
    f1.touch()
    f2 = d / "test2.rml"
    f2.touch()
    sub = d / "sub"
    sub.mkdir()
    f3 = sub / "test3.yml"
    f3.touch()
    
    # Create a file to be ignored
    f4 = d / "_ignored.yml"
    f4.touch()

    files = common.expand_files([str(d), "non_existent_file.yml"])
    assert len(files) == 4 # 3 scenarios + non_existent_file
    assert str(f1) in files
    assert str(f2) in files
    assert str(f3) in files
    assert "non_existent_file.yml" in files
    assert str(f4) not in files

def test_execution_with_exception(capsys):
    """Test exception handling during scenario execution."""
    scenario = "examples/err/bad_syntax.yml"
    assert main.reqman(None,[scenario]) == -1
    captured = capsys.readouterr()
    assert "BUG ERROR" in captured.out

def test_debug_mode(simple_scenario):
    """Test debug mode by checking if logging level is set."""
    with patch('src.reqman4.main.logging.basicConfig') as mock_config:
        main.reqman(None,[simple_scenario], is_debug=True)
        mock_config.assert_called_with(level=main.logging.DEBUG)

    with patch('src.reqman4.main.logging.basicConfig') as mock_config:
        main.reqman(None,[simple_scenario], is_debug=False)
        mock_config.assert_called_with(level=main.logging.ERROR)

def test_display_env_on_error(capsys):
    """Test that environment is displayed on error when flag is set."""
    scenario = "examples/err/bad_syntax.yml"
    assert main.reqman(None,[scenario], show_env=True) == -1
    captured = capsys.readouterr()
    assert "BUG ERROR" in captured.out
    assert "Final environment:" not in captured.out

# def test_guess_switches_from_single_file(capsys):
#     """Test guessing switches from a single file."""
#     with patch.object(sys, 'argv', ['reqman', 'examples/classic/test_switch.yml']):
#         switches = main.guess(sys.argv[1:])
#         assert 'env1' in switches
#         assert 'env2' in switches

# def test_guess_switches_from_multiple_files(capsys, tmp_path):
#     """Test guessing switches from reqman.yml when multiple files are provided."""
#     # Create a dummy reqman.yml in a temp dir
#     d = tmp_path / "project"
#     d.mkdir()
#     conf = d / "reqman.yml"
#     conf.write_text("switch:\n  env_reqman_conf:\n    doc: from conf")
#     f1 = d / "test1.yml"
#     f1.touch()
#     f2 = d / "test2.yml"
#     f2.touch()

#     with patch.object(sys, 'argv', ['reqman', str(f1), str(f2)]):
#         switches = main.guess(sys.argv[1:])
#         assert 'env_reqman_conf' in switches

# def test_guess_with_error(capsys):
#     """Test guess function when a parsing error occurs."""
#     with patch.object(sys, 'argv', ['reqman', 'examples/err/bad_syntax.yml']):
#         with pytest.raises(SystemExit):
#             main.options_from_files("switch")
#         captured = capsys.readouterr()
#         assert "START ERROR" in captured.out


def test_reqman_own_switch(tmp_path):
    """Test reqman with shebang support (-i)."""
    p_ok = tmp_path / "ok.yml"
    p_ok.write_text("""
root: http://test

--env1:
    doc: for dev
    root: http://dev/

RUN:

  - GET: /test?json=[1,2,3]
    tests:
      - len(R.json) == 3
                    """)

    original_argv = sys.argv
    sys.argv = ['reqman', str(p_ok)]
    try:
        with patch('src.reqman4.main.command') as mock_cmd:
            rc=main.reqman(None,files=[str(p_ok)])
            assert rc==0
    finally:
        sys.argv = original_argv

    original_argv = sys.argv
    sys.argv = ['reqman', str(p_ok),"--env1"]
    try:
        with patch('src.reqman4.main.command') as mock_cmd:
            rc=main.reqman(None,files=[str(p_ok)],switch="env1")
            assert rc != 0
    finally:
        sys.argv = original_argv

if __name__=="__main__":
    from pathlib import Path
    test_reqman_own_switch( Path("/tmp/"))