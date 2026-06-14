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


# The name of the case- and accent-folding collation registered below, for
# query-time ordering. Identity (the unique NOCASE columns) stays builtin and
# untouched — folding there would merge `Åsa` and `Asa` into one artist
# (ADR 0021).
FOLD_COLLATION = "FOLD"


def fold(text: str) -> str:
    """Casefold and strip diacritics, so search and sort ignore case and accents.

    SQLite's own LIKE and NOCASE only fold ASCII A–Z, so `åsa` would miss
    `Åsa`. Folding the Unicode way fixes that, and stripping diacritics goes
    one step further — `asa` finds `Åsa` too, a kindness to anyone whose
    keyboard lacks å/ä/ö. NFKD also dissolves the NFD/NFC distinction, so the
    same word matches whichever normalisation it was stored in.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold()


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


def _fold_collation(left: str, right: str) -> int:
    # The FOLD collation: ordering that ignores case and accents, so listings
    # shelve `Åsa` among the A's instead of dumping it past Z.
    left, right = fold(left), fold(right)
    return (left > right) - (left < right)


@event.listens_for(Engine, "connect")
def _configure_connection(connection, _record) -> None:
    # SQLite ships with foreign keys off; real foreign keys are a core position.
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    # Teach this connection to fold case and accents the Unicode way (see
    # `fold`): LIKE for search, and the FOLD collation for ordering. Builtin
    # NOCASE — which the unique artist/genre columns lean on for identity — is
    # left exactly as SQLite ships it.
    connection.create_function("like", 2, _like, deterministic=True)
    connection.create_function("like", 3, _like, deterministic=True)
    connection.create_collation(FOLD_COLLATION, _fold_collation)


def session(root: Path | None = None) -> Session:
    """A session against the migrated library database at the root."""
    if root is None:
        root = library_root()
    migrate(root)
    return Session(create_engine(database_url(root)))
