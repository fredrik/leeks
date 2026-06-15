"""The path source parser: claims read from a directory name (ADR 0008).

The bulk of the verification is the harness in tests/fixtures/path_names.toml:
each directory name maps to the claims expected of it, and the grammar is built
against that table. The cases below pin the confidence each field carries.
"""

import tomllib
from pathlib import Path

from leeks import path_source
from leeks.path_source import FACT_CONFIDENCE, SPLIT_CONFIDENCE, YEAR_CONFIDENCE

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


def test_release_facts_are_less_certain_than_the_year():
    # medium, region, and catalogue read from a token or the label–catalogue
    # structure: recorded, but the least certain of the path's claims (ADR 0033).
    parsed = path_source.parse("Aphex Twin - Drukqs (2001) [CD] {Warp - WARPCD92}")
    by_field = {c.field: c.confidence for c in parsed}
    assert by_field["medium"] == FACT_CONFIDENCE
    assert by_field["catalogue"] == FACT_CONFIDENCE
    assert by_field["year"] == YEAR_CONFIDENCE


def test_encoding_is_measured_not_claimed():
    # [FLAC] is the encoding — a measurement read from the bytes (ADR 0007), not
    # a release fact. The path strips it and claims nothing from it (ADR 0033).
    parsed = path_source.parse("Artist - Album (2000) [FLAC]")
    assert {c.field for c in parsed} == {"artist", "title", "year"}


def test_the_medium_casing_is_normalised_to_the_canonical_spelling():
    # The medium vocabulary is controlled, so any casing claims the one
    # canonical spelling (ADR 0034) — and "CD" is not title-cased to "Cd".
    media = {
        path_source.parse(f"A - B ({token})")[-1].value
        for token in ("vinyl", "ViNyL", "VINYL", "cd", "Cd")
    }
    assert media == {"Vinyl", "CD"}
