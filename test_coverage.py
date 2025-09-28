# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2025 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/reqman4
# #############################################################################
import sys
from unittest.mock import patch, AsyncMock
import pytest
import click
import httpx
from reqman4 import main

def test_main_entrypoint():
    """Test the main entrypoint of the application."""
    if 'reqman4.__main__' in sys.modules:
        del sys.modules['reqman4.__main__']
    with patch('reqman4.main.command') as mock_command:
        import reqman4.__main__
        mock_command.assert_called_once()

@patch("reqman4.scenario.ehttp.call", new_callable=AsyncMock)
def test_main_vars_option(mock_ehttp_call, tmp_path, monkeypatch):
    """Test the -s/--vars command-line option."""
    # Mock the http call to return a valid httpx.Response
    request = httpx.Request("GET", "http://test/get")
    mock_ehttp_call.return_value = httpx.Response(200, request=request)

    (tmp_path / "reqman.yml").write_text("root: http://test")
    (tmp_path / "a.yml").write_text("""
RUN:
  - GET: /get
    tests:
     - R.status == 200
""")
    monkeypatch.chdir(tmp_path)
    ctx = click.Context(main.command)
    assert main.reqman(ctx, files=["a.yml"], switchs=[], vars="foo=bar") == 0
    mock_ehttp_call.assert_called_once()

# def test_main_no_files(capsys):
#     """Test the command with no file arguments."""
#     ctx = click.Context(main.command)
#     assert main.reqman(ctx, files=[]) == 0
#     captured = capsys.readouterr()
#     assert "Error: Missing argument 'FILES...'" in captured.out,captured.out

def test_main_no_reqman_conf(tmp_path, monkeypatch, capsys):
    """Test running a scenario without a reqman.yml file."""
    (tmp_path / "a.yml").write_text("RUN:\n  - GET: /get")
    monkeypatch.chdir(tmp_path)
    ctx = click.Context(main.command)
    assert main.reqman(ctx, files=["a.yml"]) == -1
    captured = capsys.readouterr()
    assert "url must start with http, found /get" in captured.out

def test_main_with_rqexception(tmp_path, monkeypatch):
    """Test scenario execution with an RqException."""
    (tmp_path / "a.yml").write_text("RUN: []")
    (tmp_path / "reqman.yml").write_text("- not a dict")
    monkeypatch.chdir(tmp_path)
    ctx = click.Context(main.command)
    assert main.reqman(ctx, files=["a.yml"]) == -1

def test_main_with_generic_exception(tmp_path, monkeypatch):
    """Test the main error handler for generic exceptions."""
    (tmp_path / "a.yml").write_text("RUN: []")
    monkeypatch.chdir(tmp_path)
    with patch("reqman4.main.ExecutionTests.__init__", side_effect=Exception("generic error")):
        ctx = click.Context(main.command)
        assert main.reqman(ctx, files=["a.yml"]) == -1

@patch("reqman4.main.command")
def test_main_shebang(mock_command, tmp_path, monkeypatch):
    """Test shebang support with the -i flag."""
    a_yml = tmp_path / "a.yml"
    a_yml.write_text("""#!rq -s root=http://test/
RUN:
  - GET: /get
""")
    monkeypatch.chdir(tmp_path)
    ctx = click.Context(main.command)
    # The shebang logic re-invokes the command, so we patch it to prevent recursion
    main.reqman(ctx, files=[str(a_yml)], is_shebang=True)
    mock_command.assert_called_once()
    # Check that sys.argv was modified correctly
    assert sys.argv[1:] == [str(a_yml), '-s', 'root=http://test/']