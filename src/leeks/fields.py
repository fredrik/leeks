"""The claim-field registry: the one declaration of the claim layer.

Every field a source can assert about an album or track is declared here
once (ADR 0025), with its arity (single or set-valued, ADR 0022), the
pipeline-model attribute it reads from, and — when it is a merged scalar
column — the cast back from claim text. The write path, the merged-column
derivation, and the uniqueness the schema enforces all read from this
list, so a new claimable field is one entry here, not a change in four
places.

This module is pure declaration: it imports nothing from leeks, so the
ORM and the pipeline can both depend on it without a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ClaimField:
    """One field a source claims about one kind of entity."""

    name: str
    entity: Literal["album", "track"]
    # The text->typed cast for a merged scalar column; None when the field
    # is relational (artist FK, genre junction) or carries no column yet.
    cast: type | None = None
    # Set-valued: a source may claim several, each its own row (ADR 0022).
    multi: bool = False
    # The AlbumInfo/TrackInfo attribute, when it differs from the field name
    # (the genre field reads the plural `genres` list).
    attr: str | None = None

    @property
    def model_attr(self) -> str:
        return self.attr or self.name


# Order is the order claims are recorded and `show --sources` displays them:
# the scalars an album leads with, then its set-valued genre.
CLAIMS: tuple[ClaimField, ...] = (
    ClaimField("title", "album", cast=str),
    ClaimField("artist", "album"),
    ClaimField("year", "album", cast=int),
    ClaimField("tracktotal", "album"),
    ClaimField("genre", "album", multi=True, attr="genres"),
    ClaimField("title", "track", cast=str),
    ClaimField("artist", "track"),
    ClaimField("track", "track", cast=int),
)


def merged_fields(entity: str) -> dict[str, type]:
    """The merged scalar columns for an entity, each mapped to its cast.

    The fields merge() copies a winning claim into; relational and
    column-less fields (no cast) are absent, as they are not merged columns.
    """
    return {f.name: f.cast for f in CLAIMS if f.entity == entity and f.cast is not None}


# The set-valued field names, for the uniqueness the schema enforces: every
# other field is single-valued and gets one row per source (see orm.py).
MULTI_FIELDS: tuple[str, ...] = tuple(sorted({f.name for f in CLAIMS if f.multi}))
