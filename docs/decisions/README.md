# Decision records by subject

The records are numbered in the order they were decided, and the numbers are permanent identifiers — they never move,
and cross-links and the number bureau ([ADR 0030](0030-claim-record-numbers-from-a-bureau.md)) depend on that. This
guide groups them by subject so a reader can find every decision bearing on one area without reading the whole sequence.

It is a living reading guide, not a status index: for status, `grep '^Status' docs/decisions/*.md`. When a new record
lands, add it to its group below.

## Architecture & data model

The shape of the data and the layers that move and store it.

- [0001 — Model the pipeline in Pydantic, persist in SQLAlchemy](0001-pydantic-pipeline-sqlalchemy-persistence.md)
- [0006 — The entity hierarchy is realised as its data arrives](0006-hierarchy-by-data-availability.md)
- [0009 — Link artists now; defer the credits table to MusicBrainz](0009-artist-links-now-credits-with-musicbrainz.md)

## The claim / measurement model

How the source layer records what it is told, and how those claims are typed and constrained.

- [0007 — The source layer stores claims, not measurements](0007-claims-versus-measurements.md)
- [0008 — Claims record what sources say; the path is a source](0008-claims-record-what-sources-say.md)
- [0022 — Genre is a set-valued claim](0022-genre-is-a-set-valued-claim.md)
- [0025 — Declare claim fields in a registry](0025-declare-claim-fields-in-a-registry.md)

## The library on disk

- [0010 — The library tree is for humans](0010-the-library-tree-is-for-humans.md)

## CLI shape & verbs

The top-level interface and the verbs that ingest and surface entities.

- [0003 — Speak in verbs, not flags, at the top level](0003-verbs-not-flags.md)
- [0004 — Make `leek add` ingest exactly one album](0004-add-is-single-album.md)
- [0005 — Make `leek import` ingest a set of albums](0005-import-ingests-a-set-of-albums.md)
- [0011 — `leek list` is albums in shelf order, filtered by bare terms](0011-list-is-albums-in-shelf-order.md) —
  superseded by [0013](0013-list-selects-its-entity-by-option.md)
- [0013 — Select `leek list`'s entity by option; default to albums](0013-list-selects-its-entity-by-option.md)
- [0020 — show is one entity in depth](0020-show-is-one-entity-in-depth.md)

## Querying

The language that filters and selects.

- [0012 — Base the query language on beets](0012-query-language-is-beets-inspired.md)
- [0029 — Terms qualify by field and reach up the tree](0029-terms-qualify-by-field-and-reach-up.md)

## Output & rendering

How a selected entity becomes text — the typed projection, the field and format controls, and what the default owes.

- [0014 — Render output from a typed projection](0014-render-output-from-a-typed-projection.md)
- [0015 — Reject a template language for output](0015-reject-a-template-language-for-output.md)
- [0016 — Select fields with `--fields`](0016-select-fields-with-fields.md)
- [0017 — Choose output shape with `--format`](0017-choose-output-shape-with-format.md)
- [0018 — Discover fields with `leek fields`](0018-discover-fields-with-leek-fields.md)
- [0019 — The default output is for humans, not parsers](0019-the-default-output-is-for-humans-not-parsers.md)
- [0023 — Render a set-valued field across formats](0023-render-a-set-valued-field-across-formats.md)

## Sorting, search & locale

Folding, ordering, and the commitment to the user's language.

- [0021 — Fold case and accents for search and sort](0021-fold-case-and-accents-for-search-and-sort.md)
- [0026 — Sort in Swedish order](0026-sort-in-swedish-order.md)
- [0027 — Sort and match in the user's locale](0027-sort-and-match-in-the-users-locale.md)

## Look & theme

The palette and how fields wear colour.

- [0002 — Theme the CLI with Catppuccin Mocha](0002-catppuccin-mocha-theme.md)
- [0024 — Give each field a colour, and let the artist pop](0024-a-field-colour-vocabulary.md)
- [0028 — Select the theme with `LEEKS_THEME`](0028-select-the-theme-with-leeks-theme.md)

## The decision process itself

- [0030 — Claim decision-record numbers from a bureau](0030-claim-record-numbers-from-a-bureau.md)
