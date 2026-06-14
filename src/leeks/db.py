"""The library on disk: root resolution, database, sessions.

The root is ~/Music/leeks, overridable through $LEEKS_ROOT — the
configuration punt from the slice 1 plan. Everything leeks owns lives
under it: the database at leeks.db, copied audio in album-<id>/.
"""

import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session

MIGRATIONS = Path(__file__).parent / "migrations"


def library_root() -> Path:
    override = os.environ.get("LEEKS_ROOT")
    base = Path(override) if override else Path("~/Music/leeks")
    return base.expanduser()


def database_url(root: Path) -> str:
    return f"sqlite:///{root / 'leeks.db'}"


def migrate(root: Path) -> None:
    """Create the root and bring its database to the latest schema."""
    root.mkdir(parents=True, exist_ok=True)
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    config.set_main_option("sqlalchemy.url", database_url(root))
    command.upgrade(config, "head")


# The name of the Swedish sort collation registered below, for query-time
# ordering. Identity (the unique NOCASE columns) stays builtin and untouched —
# folding there would merge `Åsa` and `Asa` into one artist (ADR 0021).
SORT_COLLATION = "SORT"

# å, ä, ö are letters of their own in Swedish, sorting after z in that order.
# Mapping them just past `z` (which is U+007A) makes a plain string compare put
# them last; `_sort_key` strips every other diacritic, so é sorts with e.
_SWEDISH_LETTERS = str.maketrans({"å": "{", "ä": "|", "ö": "}"})


def fold(text: str) -> str:
    """Casefold and strip diacritics, so a search ignores case and accents.

    SQLite's own LIKE folds only ASCII A–Z, so `åsa` would miss `Åsa`. Folding
    the Unicode way fixes that, and stripping diacritics goes one step further —
    `asa` finds `Åsa` too, a kindness to anyone whose keyboard lacks å/ä/ö. NFKD
    also dissolves the NFD/NFC distinction, so the same word matches whichever
    normalisation it was stored in. This is for search; sorting wants the
    opposite (å/ä/ö kept distinct and last), so it has its own key below.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold()


def sort_key(text: str) -> str:
    """The Swedish sort key for `text`: case-insensitive, å/ä/ö last.

    Search folds accents away; sorting must not — a Swede reads `Åsa` at the
    bottom of the shelf, after Z, not among the A's, with å < ä < ö. So this
    casefolds (NFC first, to fold decomposed input too), parks the three
    Swedish letters just past z, then strips any remaining diacritic so foreign
    accents (é, ü) sort with their base letter rather than scattering.
    """
    folded = unicodedata.normalize("NFC", text.casefold()).translate(_SWEDISH_LETTERS)
    decomposed = unicodedata.normalize("NFKD", folded)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


@lru_cache(maxsize=512)
def _like_regex(pattern: str, escape: str | None) -> re.Pattern[str]:
    """Compile a folded SQL LIKE pattern to a regex.

    `%` matches any run, `_` any single character, and `escape` makes the
    next character literal — the LIKE contract, applied to folded text so the
    match ignores case and accents. Compiled patterns are cached because the
    same `%term%` is tested against every row.
    """
    out: list[str] = []
    i = 0
    folded = fold(pattern)
    while i < len(folded):
        char = folded[i]
        if escape and char == escape and i + 1 < len(folded):
            out.append(re.escape(folded[i + 1]))
            i += 2
        elif char == "%":
            out.append(".*")
            i += 1
        elif char == "_":
            out.append(".")
            i += 1
        else:
            out.append(re.escape(char))
            i += 1
    return re.compile("".join(out), re.DOTALL)


def _like(
    pattern: str | None, value: str | None, escape: str | None = None
) -> int | None:
    # Overrides SQLite's LIKE operator (which folds only ASCII) with a
    # Unicode-aware match. NULL on either side yields NULL, as in SQL.
    if pattern is None or value is None:
        return None
    return 1 if _like_regex(pattern, escape).fullmatch(fold(value)) else 0


def _sort_collation(left: str, right: str) -> int:
    # The SORT collation: case-insensitive Swedish order, å/ä/ö last (see
    # `sort_key`).
    left, right = sort_key(left), sort_key(right)
    return (left > right) - (left < right)


@event.listens_for(Engine, "connect")
def _configure_connection(connection, _record) -> None:
    # SQLite ships with foreign keys off; real foreign keys are a core position.
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    # Two query-time behaviours SQLite's ASCII defaults get wrong: search, which
    # should fold case and accents (the LIKE override, see `fold`), and order,
    # which should follow Swedish (the SORT collation, see `sort_key`). Builtin
    # NOCASE — which the unique artist/genre columns lean on for identity — is
    # left exactly as SQLite ships it.
    connection.create_function("like", 2, _like, deterministic=True)
    connection.create_function("like", 3, _like, deterministic=True)
    connection.create_collation(SORT_COLLATION, _sort_collation)


def session(root: Path | None = None) -> Session:
    """A session against the migrated library database at the root."""
    if root is None:
        root = library_root()
    migrate(root)
    return Session(create_engine(database_url(root)))
