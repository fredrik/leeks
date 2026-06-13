"""The fields command: the field namespace a subject exposes (ADR 0018).

`leek fields` is the discovery side of `list --fields` — it must report
exactly the names `--fields` accepts, so the two can never disagree.
"""

import json

from click.testing import CliRunner

from leeks import library
from leeks.cli import leek
from test_harness import by_title


def test_fields_defaults_to_albums():
    result = CliRunner().invoke(leek, ["fields"])
    assert result.exit_code == 0
    # Albums by default, one name per line, in column order (ADR 0016/0018).
    assert result.stdout.splitlines() == ["artist", "year", "title"]


def test_fields_albums_option_matches_the_default():
    explicit = CliRunner().invoke(leek, ["fields", "--albums"])
    default = CliRunner().invoke(leek, ["fields"])
    assert explicit.exit_code == 0
    assert explicit.stdout == default.stdout


def test_fields_tracks():
    result = CliRunner().invoke(leek, ["fields", "--tracks"])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["artist", "album", "number", "title"]


def test_fields_artists():
    result = CliRunner().invoke(leek, ["fields", "--artists"])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["name"]


def test_fields_needs_no_library():
    # The namespace is static: no album added, no database, still reports.
    result = CliRunner().invoke(leek, ["fields", "--tracks"])
    assert result.exit_code == 0
    assert "number" in result.stdout


def test_fields_subject_options_are_mutually_exclusive():
    # Shared flag_value: the last subject on the line wins, mirroring list
    # (an explicit error is the deferred mutual-exclusion question, ADR 0013).
    result = CliRunner().invoke(leek, ["fields", "--albums", "--artists"])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["name"]  # artists won


def test_fields_format_json_is_an_array_of_names():
    result = CliRunner().invoke(leek, ["fields", "--tracks", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == ["artist", "album", "number", "title"]


def test_fields_format_json_defaults_to_albums():
    result = CliRunner().invoke(leek, ["fields", "--format", "json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == ["artist", "year", "title"]


def test_fields_format_human_matches_the_default():
    # --format human is the explicit name for the bare-names default (ADR 0019).
    explicit = CliRunner().invoke(leek, ["fields", "--format", "human"])
    default = CliRunner().invoke(leek, ["fields"])
    assert explicit.exit_code == 0
    assert explicit.stdout == default.stdout


def test_fields_invalid_format_is_rejected():
    result = CliRunner().invoke(leek, ["fields", "--format", "xml"])
    assert result.exit_code != 0


def test_fields_appears_in_help():
    result = CliRunner().invoke(leek, ["help"])
    assert "fields" in result.output


def test_fields_options_appear_in_help():
    result = CliRunner().invoke(leek, ["fields", "--help"])
    assert "--albums" in result.output
    assert "--tracks" in result.output
    assert "--artists" in result.output
    assert "--format" in result.output


def test_fields_namespace_agrees_with_list_fields(corpus, materialise):
    # The pairing is the point (ADR 0018): every name fields reports is a
    # name --fields accepts, and a name it does not report is rejected.
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    for subject in ("--albums", "--tracks", "--artists"):
        reported = CliRunner().invoke(leek, ["fields", subject]).stdout.splitlines()
        selected = CliRunner().invoke(
            leek, ["list", subject, "--fields", ",".join(reported)]
        )
        assert selected.exit_code == 0
        unknown = CliRunner().invoke(
            leek, ["list", subject, "--fields", "definitely_not_a_field"]
        )
        assert unknown.exit_code != 0
