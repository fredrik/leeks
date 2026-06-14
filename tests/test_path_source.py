"""The path source parser: claims read from a directory name (ADR 0008)."""

from leeks import path_source
from leeks.path_source import YEAR_CONFIDENCE


def test_parses_a_parenthesised_year():
    [claim] = path_source.parse("The Avalanches - Since I Left You (2001)")
    assert (claim.field, claim.value) == ("year", "2001")
    assert claim.confidence == YEAR_CONFIDENCE


def test_a_name_without_a_year_claims_nothing():
    # An empty parse records nothing — the path claims only what it says.
    assert path_source.parse("Polder Arcade - Tape Hiss Archipelago") == []


def test_a_bare_year_is_not_claimed_yet():
    # Only the parenthesised form this slice; bare years are ambiguous (label
    # codes, track counts) and wait for the grammar slice.
    assert path_source.parse("Artist - 2001 - Album") == []


def test_an_implausible_year_is_ignored():
    assert path_source.parse("Album (0500)") == []  # below the floor
    assert path_source.parse("Mix (9999)") == []  # above the ceiling
