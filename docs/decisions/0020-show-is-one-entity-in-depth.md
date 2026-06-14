# 0020 — show is one entity in depth

Status: Decided (2026-06-13)

## Decision

The deep-view verb is **`show`**, the counterpart to `list`: `list` is breadth (many entities, one row each, merged
values only), `show` is depth (one entity, everything known about it). The verb is `show`, not `info`: `info` is a noun,
it is tool/database vocabulary (`docker info`, `npm info`), and it is beets' word for its tag-dump, so it fails the
verbs.md test that verbs be imperative single words in the language of a record shelf. `show` pairs with `list` as a
sentence: list the albums; show me that one.

**Subject by option, mirroring `list`.** `show --albums` (default), `show --tracks`, `show --artists` — the same
selector `list` and `fields` already use ([ADR 0013](0013-list-selects-its-entity-by-option.md)). An album's view nests
its tracks and their files regardless of the option; the selector only chooses what sits at the top.

**Selection is a query, and the result is the matching entities in depth**, reusing `list`'s substring matching
([ADR 0012](0012-query-language-is-beets-inspired.md)). The three cases:

- **A unique match** (or an explicit `id:N` term) — that entity, shown in full.
- **Several matches, at a terminal** — an **in-process, fzf-style picker**: a fuzzy-filterable list of the candidates,
  and the chosen entity is shown. The picker is a tty affordance, never a gate.
- **Several matches, piped / `--format json` / no tty** — *every* match, each shown in full, one after another.
- **Zero matches** — a note on stderr, like `list`'s empty shelf ([ADR 0011](0011-list-is-albums-in-shelf-order.md));
  exit 0, not an error.

Every scriptable path either shows one entity or shows them all, so automation is never blocked on a prompt it cannot
drive — this is "primitives are non-interactive" (verbs.md). `--format json` is **always an array**, one element when
the match is unique, so a consumer parses the same shape whether the query hit one entity or ten. `id` joins the field
namespace ([ADR 0016](0016-select-fields-with-fields.md), [0018](0018-discover-fields-with-leek-fields.md)), so `id:N`
is discoverable and selectable in `list --fields`.

**The picker is shared infrastructure, not part of `show`.** `review`, `remove`, and `match` will each need to
disambiguate a query to one entity; the fuzzy chooser is a reusable in-process component, with no external-binary
dependency, themed to the project palette ([ADR 0002](0002-catppuccin-mocha-theme.md)). `show` is its first caller.

**The default view is the merged entity in depth, with measurements; the claim layer folds away.** For an album: the
merged identity (artist, title, year, genres), the track list, and the **measurements** `list` cannot show — format,
bitrate, duration, size ([ADR 0007](0007-claims-versus-measurements.md)). Provenance — which source claimed each field —
is *not* shown by default: with a single source today it is eighteen identical `file_tags` lines.

**`--sources` unfolds the claim layer**: under each claim field, who claimed what
([ADR 0008](0008-claims-record-what-sources-say.md)). It is a human-view toggle, governing the human rendering only, and
the view where two sources agreeing or disagreeing becomes visible — where the path source's arrival (ADR 0008) first
shows.

**`--format json` always carries the full structure**, provenance included, regardless of `--sources`
([ADR 0017](0017-choose-output-shape-with-format.md), [0019](0019-the-default-output-is-for-humans-not-parsers.md)): the
nested, typed projection of the whole entity — album → fields → claims, album → tracks → files → measurements. The
`--sources` fold is presentation; JSON is the contract.

## Context

The source layer ([ADRs 0007](0007-claims-versus-measurements.md), [0008](0008-claims-record-what-sources-say.md)) is so
far invisible to users. `list` shows only merged values by design ([ADR 0011](0011-list-is-albums-in-shelf-order.md))
and measurements have no home there at all, so a verb for one-entity-in-depth is where both surface and the
claims-vs-measurements model becomes legible: merged value on top, measurements alongside, claims beneath on request.

The verb map charted this slot as `info`, "one entity in depth — including its source layer, not just the merge." This
record keeps the depth and renames the verb, but puts provenance behind `--sources`: the default distinction from `list`
is depth plus measurements, and the claim layer is what `show` reaches when asked.

## Alternatives considered

- **Keep the name `info`** — rejected: it is a noun, it is database/tool vocabulary, and it implies parity with beets'
  tag-dump that does not hold.
- **Name it `inspect`** — the serious rival, imperative and apt for provenance/measurement scrutiny, but rejected: its
  register is ops and containers (`docker inspect`, `kubectl describe`), not a record shelf. `show` wins on the
  `list`/`show` pairing and on plainness.
- **Show provenance by default** — the verb map's original charter; rejected because with one source it is pure noise.
  Folding it behind `--sources` loses nothing, as the JSON contract carries the full structure regardless.
- **Album-centric only, no `--tracks`/`--artists` subject** — rejected for breaking the
  `--albums`/`--tracks`/`--artists` symmetry `list` and `fields` established, and for denying a direct deep view of a
  track or an artist.
- **Raw integer IDs as the primary handle** — rejected: IDs are not shelf vocabulary, and it would force `list` to
  surface IDs before `show` could be used at all. `id:N` survives as an explicit, opt-in handle beside the query.
- **Refuse on ambiguity instead of showing all** — rejected: it makes the tool withhold what it already found and forces
  a re-query for data in hand. Showing all matches gives the same navigation without throwing away work.

## Consequences

The exact human rendering — how files nest under a multi-file track, how the `--sources` block aligns, how confidence
shows when an analyzer source lands ([ADR 0007](0007-claims-versus-measurements.md)) — and the JSON envelope's nested
shape are designed when the slice is built. The chooser's internals are likewise deferred: whether it builds on a tty
toolkit or a small library, its key bindings, and how its fuzzy ranking works (the matcher already carries `jellyfish`
for string similarity).
