"""The path source: claims read from a release's directory name (ADR 0008).

A second, local source. A filesystem name carries real release metadata —
artist, title, year, medium, catalogue number — that file tags often lack.
Reading it is heuristic, so the path source is an analyzer (ADR 0007): its
claims carry confidence.

The grammar is the common scene shape, `Artist - Album (Year) [Encoding]
{Label - Cat#}`, and is deliberately conservative: it claims artist and title
only from an explicit " - " split, staying silent rather than guessing. Every
bracketed group — `(...)`, `[...]`, `{...}` — is classified by its *content*,
not its bracket: the bracket is punctuation, the content is the fact (ADR
0033). A four-digit number in parens is the year; a known medium, region, or a
label–catalogue brace becomes that claim; everything else — the `[FLAC]`
encoding among it, which is a measurement, not a claim (ADR 0007) — is stripped
and claimed as nothing. The harness in tests/fixtures/path_names.toml is the
verifier this grammar is built against.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A bracketed group of any kind — "(2001)", "[FLAC]", "{Label - CAT#}". One scan
# classifies every group by content; the same scan, blanked, leaves the
# artist/title. Stripping the groups before the split also keeps a brace's own
# " - " from being read as the artist separator.
_GROUP = re.compile(r"([(\[{])([^)\]}]*)[)\]}]")

# The artist/album boundary: a spaced hyphen, never a bare one, so hyphenated
# names ("Selected Ambient Works 85-92", "Jean-Luc") stay intact.
_SEPARATOR = " - "

# A release's medium — its physical form, what MusicBrainz calls its "format".
# Distinct from the encoding ([FLAC]), which is read from the bytes (ADR 0007)
# and never claimed. A small closed vocabulary mapping the case-folded token to
# its canonical spelling: "vinyl"/"ViNyL" mean one medium, so the claim is the
# canonical "Vinyl" (ADR 0034), not the directory's casing. Grows with the
# harness, like the grammar itself.
_MEDIA = {"vinyl": "Vinyl", "cd": "CD", "cassette": "Cassette", "digital": "Digital"}

# Regions appear unreliably and open-endedly, so a closed set catches the
# unambiguous tokens and stays silent on the rest. Also grows with the harness.
_REGIONS = frozenset(
    {"eu", "europe", "us", "usa", "uk", "japan", "scandinavia", "worldwide"}
)

# A parenthesised year is rarely anything else; the dash split is the common
# convention but less certain; the release facts are recognised from a token or
# the label–catalogue structure, less certain again. All are recorded, none yet
# decides the merge (ADR 0031) — priority does.
YEAR_CONFIDENCE = 0.9
SPLIT_CONFIDENCE = 0.7
FACT_CONFIDENCE = 0.6


@dataclass(frozen=True)
class PathClaim:
    """One claim the path parser makes about the album, with its confidence."""

    field: str
    value: str
    confidence: float


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _year(content: str) -> str | None:
    """A plausible four-digit year, or None — the bounds AlbumInfo.year accepts."""
    text = content.strip()
    if text.isdigit() and len(text) == 4 and 1000 <= int(text) <= 2999:
        return text
    return None


def _fact(opener: str, content: str) -> PathClaim | None:
    """The release fact a non-year group asserts, or None (ADR 0033)."""
    text = _clean(content)
    folded = text.casefold()
    if folded in _MEDIA:
        return PathClaim("medium", _MEDIA[folded], FACT_CONFIDENCE)
    if folded in _REGIONS:
        return PathClaim("region", text, FACT_CONFIDENCE)
    # The label–catalogue brace, "{Label - Cat#}": the label leads, the
    # catalogue follows. We claim the catalogue (clear structure) and discard
    # the label, which is an entity of its own and waits for a reason.
    if opener == "{" and _SEPARATOR in text:
        catalogue = text.split(_SEPARATOR, 1)[1].strip()
        if catalogue:
            return PathClaim("catalogue", catalogue, FACT_CONFIDENCE)
    return None


def parse(name: str) -> list[PathClaim]:
    """The claims a directory name makes, by the common scene shape (ADR 0008)."""
    year: str | None = None
    facts: list[PathClaim] = []
    for opener, content in _GROUP.findall(name):
        # A bare year is ambiguous (a label code, a track count), so only the
        # parenthesised form counts; the first such group wins.
        if year is None and opener == "(" and (found := _year(content)) is not None:
            year = found
            continue
        if (fact := _fact(opener, content)) is not None:
            facts.append(fact)

    claims: list[PathClaim] = []
    working = _clean(_GROUP.sub(" ", name))
    if _SEPARATOR in working:
        artist, title = (part.strip() for part in working.split(_SEPARATOR, 1))
        if artist:
            claims.append(PathClaim("artist", artist, SPLIT_CONFIDENCE))
        if title:
            claims.append(PathClaim("title", title, SPLIT_CONFIDENCE))
    if year is not None:
        claims.append(PathClaim("year", year, YEAR_CONFIDENCE))
    claims.extend(facts)
    return claims
