import importlib.metadata
import os
import subprocess

from click.testing import CliRunner

from leeks.cli import leek


def test_version_reports_package_metadata():
    result = CliRunner().invoke(leek, ["--version"])
    assert result.exit_code == 0
    assert importlib.metadata.version("leeks") in result.output


def test_help_describes_the_project():
    result = CliRunner().invoke(leek, ["--help"])
    assert result.exit_code == 0
    assert "music library organiser" in result.output


def test_bare_invocation_greets_with_help():
    result = CliRunner().invoke(leek, [])
    assert result.exit_code == 0
    assert "music library organiser" in result.output


def test_no_ansi_codes_when_output_is_not_a_terminal():
    result = CliRunner().invoke(leek, ["--help"])
    assert "\x1b[" not in result.output


def test_help_wears_mocha_when_colour_is_forced():
    env = {**os.environ, "FORCE_COLOR": "1", "COLORTERM": "truecolor"}
    result = subprocess.run(["leek", "--help"], capture_output=True, text=True, env=env)
    assert result.returncode == 0
    # Catppuccin Mocha mauve (#cba6f7) as a truecolor escape sequence.
    assert "38;2;203;166;247" in result.stdout


def test_console_script_resolves():
    # CliRunner never exercises the [project.scripts] wiring; this does.
    result = subprocess.run(["leek", "--version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert importlib.metadata.version("leeks") in result.stdout
