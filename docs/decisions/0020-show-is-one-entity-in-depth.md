# 0020 — show is one entity in depth

Status: Decided (2026-06-13)

## Decision

The deep-view verb is **`show`**, and it is the counterpart to `list`: where `list` is breadth — many entities, one row
each, merged values only — `show` is depth — one entity, everything known about it.

**The verb is `show`, not `info`.** `info` is a noun wearing a verb's clothes and tool/database vocabulary
(`docker info`, `npm info`); it fails the verbs.md test that verbs be imperative, single words, in the language of a
record shelf. It is also beets' word for its tag-dump, so reusing it would quietly imply "the same thing," which this is
not. `show` is plain and imperative, and it pairs with `list` as a sentence: *list the albums; show me that one.*

**Subject by option, mirroring `list`.** `show --albums` (default), `show --tracks`, `show --artists` — the same
selector `list` and `fields` already use ([ADR 0013](0013-list-selects-its-entity-by-option.md)). An album's view nests
its tracks and their files regardless of the option; the selector only chooses what sits at the top.

**Selection is a query, and the result is the matching entities in depth.** `show` reuses `list`'s substring matching
([ADR 0012](0012-query-language-is-beets-inspired.md)). The query may match one entity or several, and the three cases
are:

- **A unique match** (or an explicit `id:N` term) — that entity, shown in full.
- **Several matches, at a terminal** — an **in-process, fzf-style picker**: a fuzzy-filterable list of the candidates,
  and the chosen entity is shown. The picker is a convenience for a human — a way to narrow many to one without
  scrolling past full dumps — never a gate.
- **Several matches, piped / `--format json` / no tty** — *every* match, each shown in full. JSON is an array of entity
  objects; the human-plain rendering is the matches one after another. Nothing is withheld and nothing prompts.

The only empty case is zero matches: a note on stderr, like `list`'s empty shelf
([ADR 0011](0011-list-is-albums-in-shelf-order.md)) — exit 0, not an error. This reconciles with "primitives are
non-interactive" (verbs.md): the picker is strictly a tty affordance; every scriptable path either shows one entity or
shows them all, so automation is never blocked on a prompt it cannot drive. To keep the machine shape stable,
`--format json` is **always an array** — one element when the match is unique — so a consumer parses the same shape
whether the query hit one entity or ten. `id` joins the field namespace ([ADR 0016](0016-select-fields-with-fields.md),
[0018](0018-discover-fields-with-leek-fields.md)) so `id:N` is discoverable and selectable in `list --fields`.

**The picker is shared infrastructure, not part of `show`.** Disambiguating a query to a single entity is a need
`review`, `remove`, and `match` will each have; the fuzzy chooser is built as a reusable component, in-process so it has
no external-binary dependency and themes to the project palette ([ADR 0002](0002-catppuccin-mocha-theme.md)). `show` is
simply its first caller.

**The default view is the merged entity in depth, with measurements; the claim layer folds away.** For an album: the
merged identity (artist, title, year, genres), the track list, and the **measurements** `list` cannot show — format,
bitrate, duration, size ([ADR 0007](0007-claims-versus-measurements.md)). Provenance — which source claimed each field —
is *not* shown by default. With a single source today, a provenance block is eighteen identical `file_tags` lines: noise
that tires the eye and teaches nothing.

**`--sources` unfolds the claim layer.** Under each claim field, who claimed what
([ADR 0008](0008-claims-record-what-sources-say.md)). This is the view where two sources agreeing or disagreeing becomes
visible — the payoff the source layer was built for, and where the path source's arrival (ADR 0008) will first show. It
is a *human-view toggle*: it governs the human rendering only.

**`--format json` always carries the full structure**, provenance included, regardless of `--sources`
([ADR 0017](0017-choose-output-shape-with-format.md), [0019](0019-the-default-output-is-for-humans-not-parsers.md)). The
`--sources` fold is an argument about reading, not about data: redundant lines tire a human eye, but a machine wants
everything and pays no such cost. So JSON is the nested, typed projection of the whole entity — album → fields → claims,
album → tracks → files → measurements — and `--sources` does not touch it. This keeps the human/machine split clean:
`--sources` is presentation; JSON is the contract.

## Context

The source layer ([ADRs 0007](0007-claims-versus-measurements.md), [0008](0008-claims-record-what-sources-say.md)) is,
so far, invisible. The project went to real trouble to record that file tags are claims of a `file_tags` source, that
the path will be a second source, that consensus is unanimity-or-nothing — and a user can see none of it. `list` shows
only merged values by design ([ADR 0011](0011-list-is-albums-in-shelf-order.md)); measurements have no home there at
all. A verb for one-entity-in-depth is where both finally surface, and where the claims-vs-measurements model becomes
legible: merged value on top, measurements alongside, claims beneath on request.

The verb map already charted this slot as `info`, "one entity in depth — including its source layer, not just the
merge." This record keeps the *depth*, renames the *verb*, and revises the *charter*: with provenance behind
`--sources`, the source layer is the verb's reach, not its everyday face. The default distinction from `list` is depth
plus measurements, which is real and sufficient on its own; the claim layer is what `show` can reach when asked.

## Alternatives considered

- **Keep the name `info`** — familiar from other tools and from beets, but it is a noun, it is database/tool vocabulary,
  and it implies parity with beets' tag-dump that does not hold. `inspect` was the serious rival to `show`: imperative,
  and its meaning ("examine closely") fits the provenance/measurement scrutiny well — but its register is ops and
  containers (`docker inspect`, `kubectl describe`), not a record shelf. `show` wins on the `list`/`show` pairing and on
  plainness, which is right for a primitive verb.
- **Show provenance by default** — the verb map's original charter. Honest, and ready for a second source, but with one
  source it is pure noise; folding it behind `--sources` keeps the default legible and loses nothing, because the JSON
  contract carries the full structure regardless.
- **Album-centric only — no `--tracks`/`--artists` subject** — simpler, and an album's view nests tracks and files
  anyway. Rejected for breaking the `--albums`/`--tracks`/`--artists` symmetry `list` and `fields` established, and for
  denying a direct deep view of a track or an artist.
- **Raw integer IDs as the primary handle** — unambiguous and trivial, but IDs are not shelf vocabulary, and it would
  force `list` to surface IDs before `show` could be used at all. `id:N` survives as an explicit, opt-in handle beside
  the query, not as the front door.
- **Refuse on ambiguity instead of showing all** — the first proposal: a multi-match always errors with the candidate
  list, pointing at `list` and `id:N`. Coherent with "one entity in depth" taken literally, but it makes the tool
  withhold what it already found and matched, and forces the user to re-query for data in hand. Showing all matches (a
  picker to narrow on a tty, the full set when piped) gives the same navigation without throwing away work — and the
  picker is the better terminal experience than a re-typed query.

## Grammar deferred to contact

The exact human rendering — how files nest under a multi-file track, how the `--sources` block aligns, how confidence
shows when an analyzer source lands ([ADR 0007](0007-claims-versus-measurements.md)) — and the JSON envelope's nested
shape are designed when the slice is built. The chooser's internals are likewise deferred: whether it is built directly
on a tty toolkit or borrows a small library, its key bindings, and how its fuzzy ranking works (the matcher already
carries `jellyfish` for string similarity). This record fixes the verb, its selector, the three match cases, the
default-versus-`--sources` division, and the JSON-always-array rule.
