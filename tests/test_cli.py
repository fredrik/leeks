import importlib.metadata
import os
import subprocess

from click.testing import CliRunner

from leeks import theme
from leeks.cli import leek


def test_bare_invocation_shows_about():
    result = CliRunner().invoke(leek, [])
    assert result.exit_code == 0
    assert "music library organiser" in result.output
    assert "leek help" in result.output


def test_about_is_shorter_than_help():
    about = CliRunner().invoke(leek, []).output
    full_help = CliRunner().invoke(leek, ["help"]).output
    assert len(about.splitlines()) < len(full_help.splitlines())


def test_version_command_reports_package_metadata():
    result = CliRunner().invoke(leek, ["version"])
    assert result.exit_code == 0
    assert importlib.metadata.version("leeks") in result.output


def test_help_command_lists_the_verbs():
    result = CliRunner().invoke(leek, ["help"])
    assert result.exit_code == 0
    assert "music library organiser" in result.output
    assert "version" in result.output
    assert "help" in result.output


def test_help_flag_still_answers():
    result = CliRunner().invoke(leek, ["--help"])
    assert result.exit_code == 0
    assert "music library organiser" in result.output


def test_no_ansi_codes_when_output_is_not_a_terminal():
    for args in ([], ["version"], ["help"]):
        result = CliRunner().invoke(leek, args)
        assert "\x1b[" not in result.output


def test_rainbow_cycles_the_accent_palette():
    text = theme.rainbow("leek", offset=1)
    assert text.plain == "leek"
    styles = [span.style for span in text.spans]
    cycle = theme.RAINBOW
    assert styles == [f"bold {cycle[(i + 1) % len(cycle)]}" for i in range(4)]


def test_help_wears_mocha_when_colour_is_forced():
    env = {**os.environ, "FORCE_COLOR": "1", "COLORTERM": "truecolor"}
    result = subprocess.run(["leek", "help"], capture_output=True, text=True, env=env)
    assert result.returncode == 0
    # Catppuccin Mocha mauve (#cba6f7) as a truecolor escape sequence.
    assert "38;2;203;166;247" in result.stdout


def test_console_script_resolves():
    # CliRunner never exercises the [project.scripts] wiring; this does.
    result = subprocess.run(["leek", "version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert importlib.metadata.version("leeks") in result.stdout
