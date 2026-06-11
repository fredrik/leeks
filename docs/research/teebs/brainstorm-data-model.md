# Data Model Brainstorm

> Carried over from teebs@c761a9b, trimmed and edited. Most of the original brainstorm was absorbed into
> [data-model.md](data-model.md) and [vision.md](vision.md) — the annoyances, the import state machine, layered
> metadata, normalized external IDs. What remains here are the ideas that live nowhere else: the prior-art survey behind
> the decomposed import, and the design seeds for several items the vision defers with "design later".

## Prior art: ingest and process as separate concerns

The decomposed import (`add` → `match` → `review` → `organize`, each independently runnable, queue state in the
database) is not a novel pattern — it is how most mature media tooling works:

- **Lidarr/Radarr** — the closest analogy. Explicit wanted/queued/downloading/imported pipeline with persistent state
  and auto-accept thresholds.
- **Photo management (Digikam, Lightroom)** — import registers files; tagging, face recognition, and geotagging happen
  as separate later passes.
- **Email (mbsync + notmuch)** — fetch, index, and read are independent steps.
- **Git** — the staging area separates "intend to commit" from "commit".

Beets is unusual in *not* splitting these phases.

## Acquisition provenance

Where did this album come from — a rip, a Bandcamp purchase, a download, a friend? First-class field(s), set during
import.

This is distinct from metadata-source provenance, which the source layer covers: the source layer answers "who said this
album is from 2001", acquisition provenance answers "where the files themselves came from". For collections built from
provenance-rich sources, the acquisition story is part of what the album is.

## Duplicate and variant management

Deferred in the vision ("design later"); the seed:

- The same album acquired from two sources should be tracked explicitly as two acquisitions, not collapsed or rejected
  as a duplicate.
- A FLAC and an MP3 of the same album are format variants of one logical album, and should be linked as such — one album
  entity, multiple realisations.

## Relationships

Deferred in the vision ("design later"); the seed:

- "This track is a remix of that track."
- "This album is a remaster of that album."
- "This compilation contains tracks from these albums."

## Listening history

Deferred in the vision ("design later"); the seed: play counts, last played, and similar listening data should be
first-class when they arrive — designed into the model, not bolted on the way beets plugins graft them into flexible
attributes.

## Attachments beyond cover art

The vision's defer row covers only an album-art table (multiple images); the seed is wider: N associated files per
album/track, of any kind — covers (front, back, disc), booklets, liner notes, cue sheets, rip logs. The non-image kinds
matter for provenance-rich collections, where the log is part of what the album is.

## User-defined labels

Distinct from genres, moods, and themes, which the model covers as source-provided taxonomy: free-form personal labels
like "good for running" or "party music". User-assigned, never fetched, never overwritten by a source.
