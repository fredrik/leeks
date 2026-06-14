"""The show command at the CLI surface: an album in depth, its sources, its JSON."""

import json

from click.testing import CliRunner

from leeks import library
from leeks.cli import leek
from test_harness import by_title


def test_show_prints_an_album_in_depth(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["show", "sleepwalkers"])
    assert result.exit_code == 0
    out = result.stdout
    assert "Tin Hatch Choir" in out
    assert "Cartography for Sleepwalkers" in out
    assert "2019" in out
    assert "Indie Rock" in out
    assert "Glass Harbour" in out
    assert "kbps" in out  # a measurement the shelf never shows (ADR 0007)


def test_show_default_view_folds_provenance_away(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["show", "sleepwalkers"])
    # The claim layer is behind --sources; the default view does not show it.
    assert "file_tags" not in result.stdout


def test_show_sources_unfolds_the_claim_layer(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["show", "sleepwalkers", "--sources"])
    assert result.exit_code == 0
    assert "file_tags" in result.stdout
    assert "title" in result.stdout
    assert "artist" in result.stdout


def test_show_format_json_is_a_nested_array(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["show", "sleepwalkers", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert isinstance(payload, list) and len(payload) == 1
    album = payload[0]
    assert album["year"] == 2019  # a real int, not a string (ADR 0014)
    assert album["title"] == "Cartography for Sleepwalkers"
    assert album["genres"] == ["Indie Rock"]
    assert len(album["tracks"]) == 5
    file = album["tracks"][0]["files"][0]
    assert file["format"] in {"FLAC", "MP3"}
    assert isinstance(file["size"], int)
    # Claims ride along in JSON even without --sources (ADRs 0019/0020).
    assert any(claim["source"] == "file_tags" for claim in album["claims"])


def test_show_json_is_an_array_even_for_a_single_match(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    salt = next(a for a in library.list_albums() if "Cartography" in a.title)
    result = CliRunner().invoke(leek, ["show", f"id:{salt.id}", "--format", "json"])
    assert result.exit_code == 0
    assert isinstance(json.loads(result.stdout), list)


def test_show_id_term_selects_exactly_one(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    salt = next(a for a in library.list_albums() if a.title == "Salt Meridian")
    result = CliRunner().invoke(leek, ["show", f"id:{salt.id}"])
    assert result.exit_code == 0
    assert "Salt Meridian" in result.stdout
    assert "Cartography" not in result.stdout


def test_show_several_matches_show_all(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["show", "tin hatch"])
    assert result.exit_code == 0
    assert "Cartography for Sleepwalkers" in result.stdout
    assert "Salt Meridian" in result.stdout


def test_show_no_match_is_a_note_not_an_error(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["show", "polka"])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "nothing on the shelf matches" in result.stderr


def test_show_empty_library_points_at_add():
    result = CliRunner().invoke(leek, ["show"])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "leek add" in result.stderr


def test_show_is_plain_when_not_a_terminal(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["show", "sleepwalkers"])
    # CliRunner's stdout is never a tty: no colour leaks into the pipe (ADR 0019).
    assert "\x1b[" not in result.stdout


def test_show_summarises_what_it_shows_on_stderr(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    # No terms: the whole shelf, with a count so a glance warns of a flood.
    all_albums = CliRunner().invoke(leek, ["show"])
    assert "showing all 2 albums" in all_albums.stderr
    # Terms: how many matched. The summary rides stderr, stdout stays clean.
    matched = CliRunner().invoke(leek, ["show", "salt"])
    assert "showing 1 matching album" in matched.stderr
    assert "showing" not in matched.stdout


def test_show_summary_is_silent_for_json(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["show", "--format", "json"])
    assert "showing" not in result.stderr


def test_show_has_no_sources_shorthand(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    # -s is not a flag: --sources stands alone (no other option is abbreviated).
    result = CliRunner().invoke(leek, ["show", "-s", "salt"])
    assert result.exit_code != 0


def test_show_appears_in_help():
    result = CliRunner().invoke(leek, ["help"])
    assert "show" in result.output
