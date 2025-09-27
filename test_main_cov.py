# -*- coding: utf-8 -*-
import pytest
import sys
from unittest.mock import patch
from src.reqman4 import main,common

@pytest.fixture
def simple_scenario():
    return "examples/ok/simple.yml"

@pytest.fixture
def switch_scenario():
    return "examples/classic/test_switch.yml"

def test_reqman_show_env(simple_scenario, capsys):
    """Test reqman with show environment flag (-e)."""
    assert main.reqman(None,[simple_scenario], is_debug=True) == 0 # respx mock will make it pass
    captured = capsys.readouterr()
    assert "Environment:" in captured.out
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
    f2 = d / "test2.yml"
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

def test_debug_mode(simple_scenario):
    """Test debug mode by checking if logging level is set."""
    with patch('src.reqman4.main.logging.basicConfig') as mock_config:
        main.reqman(None,[simple_scenario], is_debug=True)
        mock_config.assert_called_with(level=main.logging.DEBUG)

    with patch('src.reqman4.main.logging.basicConfig') as mock_config:
        main.reqman(None,[simple_scenario], is_debug=False)
        mock_config.assert_called_with(level=main.logging.ERROR)











def _create(tmp_path):
    p_ok = tmp_path / "scenar_with_switchs.yml"
    p_ok.write_text("""
                    
--default:                  #<- default one (forced on command line!)
    doc: default one
    root: http://test
                    
--env1:
    doc: for dev
    root: http://dev/

RUN:

  - GET: /test?json=[1,2,3]
    tests:
      - len(R.json) == 3
    """)

    return p_ok

def test_reqman_own_switch_default(tmp_path):
    yml_file=_create(tmp_path)
    nb_ko=main.reqman(None,files=[str(yml_file)])
    assert nb_ko==0

def test_reqman_own_switch_default_forced(tmp_path):
    yml_file=_create(tmp_path)
    nb_ko=main.reqman(None,files=[str(yml_file)],switchs=["default"])
    assert nb_ko==0

def test_reqman_own_switch_env1(tmp_path):
    yml_file=_create(tmp_path)
    nb_ko=main.reqman(None,files=[str(yml_file)],switchs=["env1"])
    assert nb_ko == 1

if __name__=="__main__":
    from pathlib import Path
    test_reqman_own_switch_default_forced( Path("/tmp/"))
    test_reqman_own_switch_env1( Path("/tmp/"))
    test_reqman_own_switch_default( Path("/tmp/"))
