# 0010 — The library tree is for humans

Status: Decided (2026-06-12)

## Decision

The on-disk library is part of the product: browsable in a file manager, portable to other machines and players,
readable without leeks. Copies land at

```
<Album Artist>/<Year> <Album Title>/<NN> <Title>.<ext>
```

derived from the **merged columns** at copy time. The rules:

- **Missing optional components vanish with their separators.** No year → `Polder Arcade/Tape Hiss Archipelago/`; no
  track number → `Pylon Hum.flac`. Nothing fabricates a `0000` or a `00`.
- **Required components are guaranteed below the path layer.** Album and track titles are NOT NULL merged columns
  (directory-name and file-stem fallbacks, ADR 0008); an album with no artist lands in the `Unknown Artist/` bucket.
- **Names are replaced, not slugged.** Case and spaces survive; only filesystem-hostile characters (path separators,
  Windows-reserved punctuation, trailing dots and spaces) are replaced.
- **Collisions are resolved case-insensitively**, counting up: `2001 Discovery`, `2001 Discovery-2`. Case-insensitive
  even on case-sensitive filesystems, because a library rsynced from Linux to macOS or Windows must not fold two
  directories into one.
- **Metadata changes never rename.** When a later source corrects a title, the path goes stale; `files.path` stays true.
  `leek organize` (later) re-derives stale paths explicitly — beets' `move`, never a side effect. Tag write-back (beets'
  `write`) is a separate, file-mutating operation and will be its own verb.

Artist identity folds case the same way: one `artists` row per case-folded name (`Daft Punk` and `Daft punk` are one
artist), with NOCASE uniqueness in the schema. The **first-seen spelling** is the display form, pending the correction
machinery (artist aliases and MusicBrainz IDs). Diacritic variants (`Björk`/`Bjork`) are not folded: ASCII folding
catches the common dupe, and folding diacritics can merge genuinely distinct names.

## Context

Slice 1's `album-<id>/` layout punted the human layout to `leek organize`. A library that cannot be browsed in a file
manager fails the joy requirement, and Fredrik's usage is the file manager as much as the CLI, so paths are born
human-readable. beets renamed files as a side effect of import and metadata edits; here renames stay explicit instead.

Case-insensitive filesystems (Windows, default macOS) cannot hold `a/` and `A/`, so both artist identity and path
collision-checking fold case rather than discovering the problem at copy-to-laptop time.

## Alternatives considered

- **`album-<id>` until organize** — the original punt; machine-friendly, human-hostile, and it made the organize slice
  carry the whole layout design anyway.
- **Year omitted from the scheme** — simpler, but `<Year> <Title>` sorts an artist's shelf chronologically, which is how
  a discography reads.
- **Slugged paths** (`tin-hatch-choir/2022-salt-meridian`) — robust and ugly; robustness is achieved with targeted
  replacement instead.
- **Renaming on metadata change** — beets' shape; couples the filesystem to every metadata mutation and violates
  "renames are explicit".
