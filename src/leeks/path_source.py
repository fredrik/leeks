"""The path source: claims read from a release's directory name (ADR 0008).

A second, local source. A filesystem name carries real release metadata —
artist, title, year, format, catalogue number — that file tags often lack.
Reading it is heuristic, so the path source is an analyzer (ADR 0007): its
claims carry confidence.

The grammar is the common scene shape, `Artist - Album (Year) [Format]
{Label - Cat#}`, and is deliberately conservative: it claims artist and
title only from an explicit " - " split, and a year only when parenthesised,
staying silent rather than guessing. Format, label, and catalogue number are
recognised — stripped so they don't pollute the title — but not yet claimed
(their own slice). The harness in tests/fixtures/path_names.toml is the
verifier this grammar is built against.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A parenthesised four-digit year, e.g. the "(2001)" in
# "The Avalanches - Since I Left You (2001)". A bare year is ambiguous (a label
# code, a track count), so only the parenthesised form counts.
_YEAR = re.compile(r"\((\d{4})\)")

# Metadata groups in brackets or braces — "[FLAC]", "{Label - CAT#}". Stripped
# before anything else so a brace's own " - " can't be read as the separator.
_BRACKETED = re.compile(r"[\[{][^\]}]*[\]}]")

# The artist/album boundary: a spaced hyphen, never a bare one, so hyphenated
# names ("Selected Ambient Works 85-92", "Jean-Luc") stay intact.
_SEPARATOR = " - "

# A parenthesised year is rarely anything else; the dash split is the common
# convention but less certain. Both are recorded, neither yet decides the merge
# (ADR 0031) — priority does.
YEAR_CONFIDENCE = 0.9
SPLIT_CONFIDENCE = 0.7


@dataclass(frozen=True)
class PathClaim:
    """One claim the path parser makes about the album, with its confidence."""

    field: str
    value: str
    confidence: float


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse(name: str) -> list[PathClaim]:
    """The claims a directory name makes, by the common scene shape (ADR 0008)."""
    claims: list[PathClaim] = []
    working = _BRACKETED.sub(" ", name)

    year_match = _YEAR.search(working)
    year = None
    # The same bounds AlbumInfo.year accepts — an implausible number is not one.
    if year_match is not None and 1000 <= int(year_match.group(1)) <= 2999:
        year = year_match.group(1)
        working = working[: year_match.start()] + working[year_match.end() :]

    working = _clean(working)
    if _SEPARATOR in working:
        artist, title = (part.strip() for part in working.split(_SEPARATOR, 1))
        if artist:
            claims.append(PathClaim("artist", artist, SPLIT_CONFIDENCE))
        if title:
            claims.append(PathClaim("title", title, SPLIT_CONFIDENCE))
    if year is not None:
        claims.append(PathClaim("year", year, YEAR_CONFIDENCE))
    return claims
