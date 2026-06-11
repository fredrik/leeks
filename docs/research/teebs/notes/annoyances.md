# Beets annoyances

> Fredrik's list of beets annoyances. Converted to markdown from `annoyances.txt` (teebs@b817be9); the verbatim original
> is in git history.

Grouped, not ordered by importance. Some removed or edited. This is the canonical definition as of Wed Apr 1 19:38:34
CEST 2026.

## Data model / schema

| ID      | Annoyance                                              |
| ------- | ------------------------------------------------------ |
| ANN-001 | Only one cover image, no other attachments             |
| ANN-008 | Albums are not the main unit                           |
| ANN-026 | Artist is not a data type                              |
| ANN-027 | Data model mirrors denormalized file format            |
| ANN-009 | Items and albums share fields but can come out of sync |
| ANN-017 | Singletons are unnecessary                             |
| ANN-018 | `mb_` fields should be in a separate table             |
| ANN-019 | `discogs_albumid` etc as first-level fields            |
| ANN-028 | Multi-value artist fields as workaround                |
| ANN-029 | "Add columns, never remove them" approach              |

## Metadata & sources

| ID      | Annoyance                                  |
| ------- | ------------------------------------------ |
| ANN-002 | No source tracking                         |
| ANN-003 | Matched metadata not kept                  |
| ANN-004 | Reliant on MusicBrainz                     |
| ANN-015 | Genres, moods, etc almost entirely missing |
| ANN-016 | MusicBrainz is slow                        |

## Tag writing & file handling

| ID      | Annoyance                                                         |
| ------- | ----------------------------------------------------------------- |
| ANN-010 | Too many tags written                                             |
| ANN-011 | No way to configure which tags are written to file                |
| ANN-023 | Connection between db fields and file tags is unclear             |
| ANN-012 | Unclear what tags are and how they connect to metadata            |
| ANN-024 | Little feedback on user errors related to db fields and file tags |
| ANN-014 | Original metadata is not preserved                                |

## Import workflow

| ID      | Annoyance                                  |
| ------- | ------------------------------------------ |
| ANN-013 | Almost impossible to edit an import        |
| ANN-021 | Import decisions not tracked or remembered |
| ANN-005 | `import -L` is a weird mechanic            |

## Observability & logging

| ID      | Annoyance                           |
| ------- | ----------------------------------- |
| ANN-022 | No event log, audit log, or any log |
