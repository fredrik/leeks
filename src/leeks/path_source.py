"""The path source: claims read from a release's directory name (ADR 0008).

A second, local source. A filesystem name carries real release metadata —
artist, title, year, format, catalogue number — that file tags often lack.
Reading it is heuristic, so the path source is an analyzer (ADR 0007): its
claims carry confidence. This slice reads only the one near-unambiguous
token, a parenthesised four-digit year; the full grammar is its own slice.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A parenthesised four-digit year, e.g. the "(2001)" in
# "The Avalanches - Since I Left You (2001)". The clearest token a directory
# name offers; bare years wait for the grammar slice, where they are ambiguous.
_YEAR = re.compile(r"\((\d{4})\)")

# High, but not certain: a parenthesised year is rarely anything else, yet
# reading a name is still a guess (ADR 0007). Recorded, not yet decisive —
# priority alone resolves the merge for now.
YEAR_CONFIDENCE = 0.9


@dataclass(frozen=True)
class PathClaim:
    """One claim the path parser makes about the album, with its confidence."""

    field: str
    value: str
    confidence: float


def parse(name: str) -> list[PathClaim]:
    """The claims a directory name makes — the parenthesised year, for now."""
    claims: list[PathClaim] = []
    match = _YEAR.search(name)
    # The same bounds AlbumInfo.year accepts (ADR-free sanity, not a real year).
    if match is not None and 1000 <= int(match.group(1)) <= 2999:
        claims.append(PathClaim("year", match.group(1), YEAR_CONFIDENCE))
    return claims
