# Verbs

The verbs are leeks' user interface. `leek` speaks in verbs, not flags (ADR 0003), so the collection of verbs *is* the
product's surface: each one is chosen with care, and the collection is curated as a whole. Adding a verb is a design
decision — it gets an ADR; this document is the living map of the collection.

## Principles

**One verb, one concern.** `add` ingests one album; `import` ingests many and owns boundary detection (ADR 0004/0005).
`organize` re-derives stale paths; tag write-back will be its own verb (ADR 0010). When a verb accumulates a second
concern, that is a new verb trying to get out — beets' importer is the cautionary tale.

**Primitives are non-interactive; orchestrators may ask.** `add` never prompts (ADR 0004); `import`, wrapping it, may —
and only about what the albums are, never about metadata quality (ADR 0005). Scriptability lives in the primitives.

**Refusals point at the right verb.** "This looks like 12 albums — try `leek import`." A refusal is navigation, not
failure.

**Mutation is explicit.** No verb modifies files, renames, or writes tags as a side effect of another verb's job (core
position: originals are never modified; renames are explicit). Verbs that mutate the library's bytes or layout do only
that, on request.

**Speak the user's vocabulary.** Imperative, single words, the language of someone with a record shelf — not database
words. `add`, not `ingest`; `review`, not `reconcile-pending-changes`.

## The collection

| Verb        | Status            | Concern                                                              |
| ----------- | ----------------- | -------------------------------------------------------------------- |
| *(bare)*    | shipped (slice 0) | The about card — greeting, not reference (ADR 0003)                  |
| `version`   | shipped (slice 0) | The version, with the sparkle                                        |
| `help`      | shipped (slice 0) | The reference                                                        |
| `add`       | shipped (slice 1) | Ingest exactly one album, non-interactively (ADR 0004)               |
| `list`      | next (slice 2)    | The library, queryable                                               |
| `info`      | next (slice 2)    | One entity in depth — including its source layer, not just the merge |
| `match`     | planned (slice 4) | MusicBrainz matching, separate and retryable                         |
| `review`    | planned (slice 5) | The pending-changes queue: accept, reject, auto-accept rules         |
| `import`    | later             | Ingest a set of albums; owns boundary detection (ADR 0005)           |
| `init`      | later             | Create a library: location and config, retiring the hardcoded root   |
| `organize`  | later             | Re-derive stale paths per ADR 0010 — beets' `move`, made explicit    |
| `remove`    | later             | Take an album out of the library (implied by ADR 0004's `--force`)   |
| *(unnamed)* | later             | Tag write-back — beets' `write`; deliberately unnamed until designed |

## Open questions

- The write-back verb's name. `write` is beets' word and database-flavoured; the right word should say "push metadata
  into the files". Not needed until the verb is.
- Whether `organize` is the right word, or whether the reconciler and a future "show me what's stale" preview are one
  verb or two.
