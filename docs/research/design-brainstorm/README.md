# The pre-contact design brainstorm

The output of an agent-run design brainstorm, 2026-06-10, written against an empty repository — the branch it lived on
(`design-notes`, commit `27e81e1`) forked from `uv init`. It is the project's own teebs in miniature: speculative design
written before implementation contact, preserved as precedent, never blueprint.

Reviewed idea by idea on 2026-06-12, filed on 2026-06-13 (the [distillation record](distillation.md)). Everything
adopted was distilled into the design docs; this directory preserves the full material and records the disposition of
all of it. The two ADR-shaped files were never adopted and their numbering predates `docs/decisions/` — their
`0001`/`0003` collide with real records and mean nothing.

## Files

| File                                             | What                                                                |
| ------------------------------------------------ | ------------------------------------------------------------------- |
| [design-notes.md](design-notes.md)               | The brainstorm itself: model, schema sketch, porcelain, VFS, stack  |
| [storage-backend.md](storage-backend.md)         | ADR-shaped: SQLite default, Postgres supported, dump as interchange |
| [actors-capabilities.md](actors-capabilities.md) | ADR-shaped: actor identity, capability tiers, one write path, MCP   |

## Reading it today

The brainstorm predates the [glossary](../../design/glossary.md); translate as you read:

| Brainstorm says     | The project says                     |
| ------------------- | ------------------------------------ |
| layer / layer entry | source / claim (in the source layer) |
| effective metadata  | merged view                          |
| `leek rebuild`      | merge (recomputing merged columns)   |
| event / event log   | the change log (a future arrival)    |
| staging / proposals | the pending-changes queue (slice 5)  |

## Adopted

Distilled into the living docs on review; the brainstorm's wording is superseded by theirs.

- **Fetched payloads are kept** → [core-positions](../../design/core-positions.md)
- **Automation writes as its own source, below `user`; no anonymous writes** → core-positions
- **The merged view is rebuildable; losing claims is data loss** → core-positions (sharpens the layers position)
- **Undo is a compensating change, never a rewrite** → core-positions (sharpens the history position)
- **One extension protocol — a plugin is a source; resist hook soup** → core-positions
- **Engine portability as discipline; the dump as canonical interchange** → [portability](../../design/portability.md),
  with the Postgres CI leg explicitly deferred
- **Review must scale to bulk proposals** → noted on the [roadmap](../../plans/2026-06-11-roadmap.md) for slice 5
- **`dump` / `load` as verbs** → the [verbs](../../design/verbs.md) collection, later

## Converged independently

Decided on main, with no sight of the brainstorm, before this review filed anything — evidence these ideas are stable:

- Tracker folder names as a metadata source → [ADR 0008](../../decisions/0008-claims-record-what-sources-say.md) (the
  path is a source)
- `artist_credit` between artist and release →
  [ADR 0009](../../decisions/0009-artist-links-now-credits-with-musicbrainz.md) (credits arrive with MusicBrainz)
- Fingerprints: deterministic bytes-fact vs heuristic identification →
  [ADR 0007](../../decisions/0007-claims-versus-measurements.md) (measurement vs analyzer claim)
- Ingest ≠ identify, user edits as a layer, pressing identity, in-process matching → core positions and the slice plans

## Parked — mine these when their slice arrives

- **Beets-style query language** (design-notes §8): field-qualified atoms (`year:2019`, ranges, negation) compiled to
  SQL over the normalised schema. The *direction* is now decided —
  [ADR 0012](../../decisions/0012-query-language-is-beets-inspired.md): leeks' query language is beets-inspired,
  preserving the terse, guessable surface that makes beets a joy. The *grammar* is still parked:
  [ADR 0011](../../decisions/0011-list-is-albums-in-shelf-order.md) set bare substring terms as the floor for
  `leek list` and punted the operators until a real query demands the design. So the brainstorm's leaning was right on
  direction; what waits is the deliberate grammar, written on typed columns rather than accreted the way beets' was.
- **The virtual filesystem** (design-notes §7). The one decision that already holds: the browse tree is a render
  function, never canonical. The one experiment worth its cost when the time comes: the **retag-on-read spike** (~50
  lines — synthesize a VORBIS_COMMENT, splice it over layer-0 tags at open time, verify in mpv) — canonical bytes stay
  untouched, so a seeding torrent keeps seeding while every other consumer sees merged metadata. The section also holds
  the engineering notes (invalidation, stable inodes, negative-lookup caching, transport-agnostic core) and prior art to
  mine for scars.
- **Capability tiers, daemon-mediated access, MCP** (actors-capabilities). Machinery for actors that don't exist yet.
  The adopted positions (own sources, no anonymous writes) are the part that had to come early; tiers, CAS-on-apply, and
  the MCP tool surface wait for the first real agent.
- **The history porcelain** (design-notes §5): `diff @2026-01-01 @now`, `diff --layers` as a source-disagreement report,
  `blame`, `edit` as an `$EDITOR` round-trip into user claims. The payoff list for the adopted invariants — each falls
  out of claims + change log + a canonical rendering, with no extra model.
- **The canonical serialisation consumer list** (design-notes §6): dump/load, diff, show/edit, a VFS sidecar, proposal
  payloads. Five consumers, one deterministic rendering — the constraint to design against when the first consumer
  arrives.
- **Acoustic fingerprints as file identity** (design-notes §4): dedupe across encodes, identity that survives retags.
  ADR 0007 already homes the raw fingerprint as a measurement; the identity idea waits on chromaprint earning its place
  in the dependency story.
- **Live vs pinned playlists** (design-notes §7): query-defined and regenerated, vs materialised and user-ordered;
  `cp live/x.m3u pinned/` freezes one.

## Open questions carried out of the brainstorm

- **Precedence configuration shape.** Only `user`-wins is fixed; where automated sources sit relative to external ones,
  and whether precedence is per-field, is merge policy — unsettled until slice 5. Punt: a single global precedence
  order, `user` on top, for now.
- **Raw payload archival.** How fetched payloads are stored, compressed, and pruned — settled when the first fetching
  source arrives (slice 4). Punt: store verbatim, compress nothing, prune never.

## Rejected

- **The medallion (bronze/silver/gold) vocabulary.** Everything it carried survives in plain project terms (payloads
  kept, merged view rebuildable, corruption asymmetry); the metaphor itself is borrowed ceremony, which the brainstorm
  warns against and then commits anyway.
- **Postgres in CI now.** A permanently doubled CI surface against a hypothetical topology. The discipline that keeps
  the door open was adopted instead ([portability](../../design/portability.md)); the second engine arrives when a
  multi-host deployment is real.
- **The brainstorm's ADR numbering and root-level placement.** Superseded by `docs/decisions/` and this taxonomy.
