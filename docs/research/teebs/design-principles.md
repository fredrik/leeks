# teebs Design Principles

> Carried over from teebs@c761a9b, lightly edited. This is the rhetorical bridge of the teebs design phase: it sits
> between the raw annoyances ([notes/](notes/), [research/beets](../beets/)) and the full design
> ([vision.md](vision.md), [data-model.md](data-model.md)), arguing each architectural departure as *what beets does →
> what teebs does → why*. leeks' [core-positions](../../design/core-positions.md) descend from this document.

## 1. Import everything, gate nothing

**Beets:** Confidence score is a gatekeeper. Below threshold → import rejected. Unmatched music is unmanaged music.

**Teebs:** Every file enters the library unconditionally. The `file_tags` source always exists. External source matches
are recorded with their confidence score but never block import.

**Why:** The files that most need management are the ones with the worst metadata. Refusing to import them is the worst
possible outcome. Confidence is metadata *about* metadata — it belongs in the source layer, not at the gate.

## 2. Import is not overwrite

**Beets:** Importing means selecting a MusicBrainz release. The match overwrites file tags, renames the file, and moves
it into the managed directory. This is a single, destructive, one-shot operation. A wrong match at 0.60 confidence means
wrong filenames and wrong tags, with no easy undo.

**Teebs:** Importing means adding a file to the library. Source data (file tags, MB match, Discogs match, etc.) is
stored in separate layers. The merged view is computed from sources according to priority rules. A wrong match is a
low-confidence source entry you can ignore or delete — nothing irreversible happened.

**Why:** The confidence threshold in beets exists because import is destructive. Remove the destruction, remove the need
for the gate. The system should be safe to use without fear.

## 3. Sources are layers, not overwrites

**Beets:** One truth. Importing a MB match replaces whatever was there. Re-importing replaces again. There is no
history, no provenance, no way to compare what MB said vs. what the file tags said vs. what Discogs says.

**Teebs:** Each metadata source is an independent layer. File tags, MusicBrainz, Discogs, user edits, plugin-provided
data — all stored separately, all preserved. The library view is a materialized merge of these layers according to
configurable priority rules.

**Why:** Metadata sources disagree. MB has a great title but wrong year. Discogs has the right year. You manually fixed
the genre. The system should preserve all of this, let you see where sources conflict, and let you choose per-field
which source wins — without destroying the others.

## 4. Confidence is recorded, not enforced

**Beets:** `strong_rec_thresh = 0.95`, `medium_rec_thresh = 0.25`. These thresholds determine whether a match is
auto-accepted, presented for confirmation, or rejected.

**Teebs:** Confidence is stored per source match. Merge rules can use confidence ("accept MB fields where confidence >
0.95, queue the rest for review") but confidence never prevents data from being stored. Low-confidence matches are
available for inspection, comparison, and future re-evaluation.

**Why:** A 0.70 match today might be the best available. Tomorrow MB might add the release and produce a 0.98 match. The
0.70 data shouldn't have been thrown away — it should have been stored, marked as low confidence, and superseded when
better data arrived.

## 5. Background fetch, foreground review

**Beets:** Import is interactive. You sit at the terminal, confirm matches one by one, or set thresholds and hope for
the best.

**Teebs:** Source fetching happens in the background — on a schedule, on demand, or at import time. Changes from sources
appear in a pending changes queue. Review happens separately: a human or an agent inspects pending changes and approves,
rejects, or edits them. Approved changes update the merged view.

**Why:** Separating fetch from review means sources can update continuously without disrupting the library. It also
means review can be automated ("auto-accept MB corrections where confidence > 0.95") or delegated to an AI agent,
without changing the architecture.

## 6. The library is always queryable

**Beets:** The library is queryable, but only the "current truth" — whatever was last imported/overwritten.

**Teebs:** Both the merged view and the individual source layers are queryable. You can ask "what does my library look
like?" (merged view) and "where do my sources disagree?" (source layer comparison). The database is plain SQLite,
queryable by any tool with standard SQL.

**Why:** Debugging metadata ("why does this track say 2003?") is a common pain point. With source tracking, the answer
is concrete: "MB says 2003 (confidence 0.91), Discogs says 2004, file tags say 2002, user override says 2003. Merged
view uses MB because it has highest priority."

## 7. Non-destructive by default

**Beets:** Importing can retag, rename, and move your entire library as a side effect.

**Teebs:** Operations that modify files (tag writing, renaming, moving) are explicit, separate actions — never side
effects of importing or matching. The database can be rebuilt from sources at any time. File operations are opt-in and
reversible where possible.

**Why:** The scariest part of beets for new users is that importing can rename and retag your entire library. Separating
"add to database" from "modify files" makes the system safe to experiment with.

## Summary

| Concern           | Beets                         | Teebs                                     |
| ----------------- | ----------------------------- | ----------------------------------------- |
| Unmatched files   | Rejected or imported bare     | Always imported, always managed           |
| Metadata source   | Single truth, last write wins | Layered, all sources preserved            |
| Confidence score  | Import gate                   | Stored metadata, used by merge rules      |
| Source updates    | Re-import (destructive)       | Background fetch → pending queue → review |
| File modification | Side effect of import         | Explicit, separate action                 |
| Provenance        | Not tracked                   | Per-field, per-source                     |
| Review            | Interactive terminal          | Async: human, agent, or automated rules   |
