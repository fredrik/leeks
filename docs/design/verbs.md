# Verbs

The verbs are leeks' user interface. `leek` speaks in verbs, so the collection of verbs is the product's surface: each
one is chosen with care, and the collection is curated as a whole. Adding a verb is a design decision. This document is
the living map of the collection.

## Principles

**One verb, one concern.** `add` ingests one album; `import` ingests many and owns boundary detection. `organize`
re-derives stale paths; tag write-back will be its own verb. When a verb accumulates a second concern, that is a new
verb trying to get out — beets' importer is the cautionary tale.

**Primitives are non-interactive; orchestrators may ask.** `add` never prompts.

**Refusals point at the right verb.** "This looks like 12 albums — try `leek import`." A refusal is navigation, not
failure.

**Mutation is explicit.** No verb modifies files, renames, or writes tags as a side effect of another verb's job. Verbs
that mutate the library's bytes or layout do only that, on request.

**Speak the user's vocabulary.** Imperative, single words, the language of someone with a record shelf — not database
words. `add`, not `ingest`; `review`, not `reconcile-pending-changes`.

## The collection

| Verb        | Status            | Concern                                                                                           |
| ----------- | ----------------- | ------------------------------------------------------------------------------------------------- |
| *(bare)*    | shipped (slice 0) | The about card — greeting, not reference                                                          |
| `version`   | shipped (slice 0) | The version, with the sparkle                                                                     |
| `help`      | shipped (slice 0) | The reference                                                                                     |
| `add`       | shipped (slice 1) | Ingest exactly one album, non-interactively                                                       |
| `list`      | shipped (slice 2) | The library, made visible — albums by default, entity by option; output via `--fields`/`--format` |
| `show`      | shipped (slice 2) | One entity in depth — merged values and measurements; `--sources` reaches the claim layer beneath |
| `fields`    | shipped (slice 2) | The field namespace a subject exposes — what `--fields` can name                                  |
| `match`     | planned (slice 4) | MusicBrainz matching, separate and retryable                                                      |
| `review`    | planned (slice 5) | The pending-changes queue: accept, reject, auto-accept rules                                      |
| `import`    | later             | Ingest a set of albums; owns boundary detection                                                   |
| `init`      | later             | Create a library: location and config, retiring the hardcoded root                                |
| `organize`  | later             | Re-derive stale paths per ADR 0010 — beets' `move`, made explicit                                 |
| `remove`    | later             | Take an album out of the library                                                                  |
| `dump`      | later             | The library as portable text: claims and history, never the merged view                           |
| `load`      | later             | Rebuild a library from a dump; merged view recomputed, not read                                   |
| *(unnamed)* | later             | Tag write-back — beets' `write`; deliberately unnamed until designed                              |

## Open questions

- The write-back verb's name. `write` is beets' word and database-flavoured; the right word should say "push metadata
  into the files". Not needed until the verb is.
- Whether `organize` is the right word, or whether the reconciler and a future "show me what's stale" preview are one
  verb or two.
- How `list` and `show` queries grow further. ADR 0029 settled the first step: a term is `[field:]value`, substring and
  ANDed, with bare terms reaching up the tree (a `--tracks` term matches the album artist) and `id:N` the exact
  selector. Still open, deferred until a real query demands them: ranges (`year:1990..1999`), comparisons, negation, OR,
  and sort terms (ADR 0012), and `genre:` once genre enters the namespace. Mutual-exclusion errors between the subject
  options (`--tracks`/`--artists`/`--genres`) remain part of that deferred grammar too; today the last option wins.
