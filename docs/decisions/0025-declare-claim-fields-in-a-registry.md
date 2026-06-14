# 0025 — Declare claim fields in a registry

Status: Decided (2026-06-14)

## Decision

The claim layer's fields are declared once, in a registry (`leeks/fields.py`): a tuple of `ClaimField`, each naming a
field a source asserts about an album or track, its arity (single or set-valued), the pipeline-model attribute it reads
from, and — when it is a merged scalar column — the cast back from claim text. Three things now read from that one
declaration instead of repeating the knowledge:

- **The write path.** `_record_claims` iterates the registry, reading each field off the `AlbumInfo`/`TrackInfo` by its
  declared attribute and recording one claim for a scalar, one-per-value for a set field — no hand-written field lists.
- **The merged columns.** `MERGED_FIELDS` is derived: a merged column is exactly a claim field carrying a cast. Adding a
  field with a cast makes it a merged column; the relational and column-less fields (artist, genre, tracktotal) have
  none and are absent.
- **The schema's arity enforcement.** The fields the registry does *not* mark set-valued get a partial unique index —
  one row per `(source, entity, field)` `WHERE field NOT IN (<set fields>)` — so the database itself bars a source from
  claiming two years for one album, while genre stays free to repeat by value.

That last point **revises ADR 0022's "arity is code, not schema."** 0022 left single-valued-ness to write-path
discipline because one set field did not justify a registry. Now that the registry exists, declaring arity once and
letting the schema enforce it costs almost nothing and retires the trust. 0022's core decision — genre is a set-valued
claim — stands unchanged; only its enforcement footnote is superseded here.

Adding a claimable field is now one entry in the registry, which drives the write path, the merge, and (with a one-line
migration when arity is involved) the index — not a coordinated edit across four places that drift apart.

## Context

Before this, the answer to "which fields can hold multiple values?" was enacted, not declared: the write path had two
hand-written loops (a scalar tuple and a genre loop), `MERGED_FIELDS` was a separate literal, the consensus helpers were
chosen by hand, and single-valued-ness was a write-path promise the schema did not back. Four places had to agree, and a
new field meant remembering all four. The uniqueness key from 0022 (`…, field, value`) barred only identical duplicates;
nothing stopped a buggy writer from recording two different years. The registry makes the knowledge a single fact and
lets the schema hold the line.

Consensus in `assemble` stays explicit rather than registry-driven: it builds a typed `AlbumInfo` with named fields, and
reading arity from the registry there would obscure more than it saves. The registry's reach is the claim layer's
fields, not the display namespace (`leek fields`) — those are a different list for good reasons (id is selectable but
not a claim; the effective artist is displayed but stored relationally).

## Alternatives considered

- **An arity-only registry, leaving `MERGED_FIELDS` separate** — a smaller change, but it would leave two field lists to
  keep in sync, which is half the duplication the registry exists to remove. If the registry is the source of truth, the
  cast belongs in it.
- **A runtime write-path guard instead of a DB index** — would assert arity from the registry before insert, but leaves
  the database ignorant; a stray writer or a future second source could still slip two scalars past it. The schema is
  the honest place for an invariant the whole system depends on.
- **An ordinal column to make every field uniformly multi-valued** — already weighed and declined in ADR 0022; a partial
  index expresses "these fields are single" without reshaping the table or inventing an order nothing reads.
