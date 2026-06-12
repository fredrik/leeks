"""The list command at the CLI surface: the shelf, and notes when it is bare."""

from click.testing import CliRunner

from leeks import library
from leeks.cli import leek
from test_harness import by_title


def test_list_prints_the_shelf_in_order(corpus, materialise):
    library.add(materialise(by_title(corpus, "Paper Lung Atlas")))
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list"])
    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert "Tin Hatch Choir" in lines[0]
    assert "2019" in lines[0]
    assert "Cartography for Sleepwalkers" in lines[0]
    assert "5 tracks" in lines[0]
    assert "Paper Lung Atlas" in lines[1]


def test_list_narrows_with_terms(corpus, materialise):
    library.add(materialise(by_title(corpus, "Paper Lung Atlas")))
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list", "sleepwalkers"])
    assert result.exit_code == 0
    assert "Cartography for Sleepwalkers" in result.stdout
    assert "Paper Lung Atlas" not in result.stdout


def test_an_empty_library_points_at_add():
    result = CliRunner().invoke(leek, ["list"])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "leek add" in result.stderr


def test_no_match_is_a_note_not_an_error(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["list", "polka"])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "nothing" in result.stderr


def test_fallbacks_render_but_are_visibly_not_data(shelve):
    shelve("Mystery Tape")
    result = CliRunner().invoke(leek, ["list"])
    assert "Unknown Artist" in result.stdout
    assert "1 track" in result.stdout


def test_piped_albums_are_one_line_each(shelve):
    # Long enough that the table rendering would wrap it at width 80.
    shelve(
        "An Album Title That Goes On Considerably Longer Than Anyone Would "
        "Reasonably Expect (Deluxe)",
        artist="The Extraordinarily Long-Winded Orchestral Collective of "
        "Greater Scandinavia",
        year=2021,
    )
    result = CliRunner().invoke(leek, ["list"])
    lines = result.stdout.splitlines()
    assert len(lines) == 1
    artist, year, title, tracks = lines[0].split("\t")
    assert artist.startswith("The Extraordinarily")
    assert year == "2021"
    assert title.endswith("(Deluxe)")
    assert tracks == "1 track"


def test_list_appears_in_help():
    result = CliRunner().invoke(leek, ["help"])
    assert "list" in result.output
