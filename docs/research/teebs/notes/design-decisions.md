# Design decisions

> Converted to markdown from `design-decisions.txt` (teebs@b817be9); the verbatim original is in git history.

## General

- **Opinionated defaults:** there is one good way to do things.
- **Import is decomposed:** scanning, matching, reviewing, and organizing are independent steps with persistent state.
- **Non-interactive by default.** Automatable, batchable. Sources are fetched async in background. User reviews at their
  leisure.
- **Proper normalization.** Artists are entities. Genres are entities. External IDs are a thing. No delimiter-separated
  strings. No denormalized album fields on tracks.
- **Everything is preserved.** Original file tags are read and stored as a layer. Matched metadata is stored as a layer.
  User edits and overrides are stored.
- **Copy on import.** Never move or otherwise modify any original files.

## Data modelling

- The 'release' is the primary unit (could be called 'album', although that word is overloaded). This is opposed to
  'item' in beets, which is derived from handling files.
- 'Artist' is an entity.
- Data models are normalized.
- 'Singletons' is not a thing.
- Sources and external IDs are modelled.
- The database should be queryable by other tools, so use standard SQL constructs (no nested JSON / BSON, no embedded
  strings that require application decoding, etc).
- Pydantic is used to validate data throughout the system.
- Pydantic data classes are the internal data class representation.
- SQLAlchemy is used to persist to storage. No other components deal directly with SQLAlchemy models or classes.

## Undecided

- Flexible attributes — what to do?
- How to model genres, styles, mood, etc?
- Are we taking the data modelling too far, too fast if we go 100% MusicBrainz with releasegroup, recording, work, etc?
- Path templates — what to do?
