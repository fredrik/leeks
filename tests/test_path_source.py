"""The path source parser: claims read from a directory name (ADR 0008).

The bulk of the verification is the harness in tests/fixtures/path_names.toml:
each directory name maps to the claims expected of it, and the grammar is built
against that table. The cases below pin the confidence each field carries.
"""

import tomllib
from pathlib import Path

from leeks import path_source
from leeks.path_source import SPLIT_CONFIDENCE, YEAR_CONFIDENCE

_HARNESS = Path(__file__).parent / "fixtures" / "path_names.toml"


def _cases():
    with _HARNESS.open("rb") as handle:
        return tomllib.load(handle)["cases"]


def test_parses_every_harness_name_as_expected():
    for case in _cases():
        got = {(c.field, c.value) for c in path_source.parse(case["name"])}
        want = {(c["field"], c["value"]) for c in case["claims"]}
        assert got == want, case["name"]


def test_the_year_is_surer_than_the_dash_split():
    parsed = path_source.parse("Boards of Canada - Geogaddi (2002)")
    by_field = {c.field: c.confidence for c in parsed}
    assert by_field["year"] == YEAR_CONFIDENCE
    assert by_field["artist"] == SPLIT_CONFIDENCE
    assert by_field["title"] == SPLIT_CONFIDENCE


def test_an_implausible_year_is_ignored():
    assert path_source.parse("Album (0500)") == []  # below the floor
    assert path_source.parse("Mix (9999)") == []  # above the ceiling
