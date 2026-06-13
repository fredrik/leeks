"""The add command at the CLI surface: cards on success, hints on refusal."""

from click.testing import CliRunner

from leeks.cli import leek
from test_harness import by_title


def test_add_prints_the_card(corpus, materialise):
    directory = materialise(by_title(corpus, "Cartography for Sleepwalkers"))
    result = CliRunner().invoke(leek, ["add", str(directory)])
    assert result.exit_code == 0
    assert "added" in result.output
    assert "Cartography for Sleepwalkers" in result.output
    assert "Tin Hatch Choir" in result.output
    assert "5 tracks" in result.output
    assert "15 values read from the file tags" in result.output


def test_add_refuses_a_tree_with_the_import_hint(corpus, materialise):
    materialise(by_title(corpus, "Salt Meridian"))
    directory = materialise(by_title(corpus, "Paper Lung Atlas"))
    result = CliRunner().invoke(leek, ["add", str(directory.parent)])
    assert result.exit_code != 0
    assert "leek import" in result.output


def test_add_refuses_a_readd(corpus, materialise):
    directory = materialise(by_title(corpus, "Paper Lung Atlas"))
    assert CliRunner().invoke(leek, ["add", str(directory)]).exit_code == 0
    result = CliRunner().invoke(leek, ["add", str(directory)])
    assert result.exit_code != 0
    assert "already added" in result.output


def test_add_appears_in_help():
    result = CliRunner().invoke(leek, ["help"])
    assert "add" in result.output
