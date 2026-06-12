# Distilling the design-notes branch

Session record, 2026-06-12 to 2026-06-13. The `design-notes` branch — one commit, `27e81e1`, an agent-run design
brainstorm from 2026-06-10, forked from `uv init` with three markdown files at the repository root — was read in full,
argued idea by idea, and dispositioned. The material now lives in
[docs/research/design-brainstorm/](../research/design-brainstorm/README.md); the branch itself is ready to delete
(Fredrik's call — the commit hash above keeps it recoverable in principle).

## Method

- Every idea on the branch was classified against main: already on main in better form, novel, or in conflict.
- The novel ideas were grouped by *when they bind* — schema-and-write-path now, interchange soon, far-future machinery —
  and argued one by one from the beets scar tissue rather than relayed on the brainstorm's authority. Fredrik reviewed
  the argued list and approved the keepers and the rejects wholesale.
- A completeness sweep against the original files then caught what the first pass dropped: the query-atom direction
  (`field:value` compiled to SQL), the precedence-configuration open question, tracker folder names as a source, and the
  `artist_credit` entity.

## The convergence

Between the review and the filing, main moved — slice 1 landed, the glossary landed, decisions 0004–0010 landed — and
three of the brainstorm's ideas (including two of the sweep's "misses") turned out to be **independently decided** in
the meantime, with no sight of the brainstorm: the path as a source (ADR 0008), credits arriving with MusicBrainz (ADR
0009), and fingerprints split into deterministic measurement versus heuristic identification claim (ADR 0007). Same
forks, same choices, reached from implementation contact rather than speculation. That is the strongest evidence the
review produced that the remaining keepers are stable — and a small vindication of the project principle that good
design re-derives itself from local information.

## Dispositions

- **Adopted into [core-positions](../design/core-positions.md):** fetched payloads are kept; automation writes as its
  own source below `user`, with no anonymous writes; the merged view is rebuildable (corruption asymmetry); undo is a
  compensating change, never a rewrite; one extension protocol — a plugin is a source of claims.
- **Adopted as discipline in [portability](../design/portability.md):** the engine-portability rules, with the Postgres
  CI leg explicitly declined until a multi-host topology is real; the dump as canonical interchange, serialising claims
  and history, never the merged view.
- **Noted on the [roadmap](../plans/2026-06-11-roadmap.md):** query atoms for slice 2; bulk-scale review for slice 5;
  the dump and the wantlist under Later. `dump`/`load` joined the [verbs](../design/verbs.md) collection as later.
- **Parked in the research README:** the virtual filesystem (with the retag-on-read spike recipe), capability tiers and
  MCP, the history porcelain, the canonical-serialisation consumer list, fingerprints-as-identity, live/pinned
  playlists. Two open questions carried out with punts: precedence configuration shape, raw-payload archival.
- **Rejected:** the medallion vocabulary (kept the freight, dropped the words), Postgres in CI now, the brainstorm's ADR
  numbering.

## Lessons

- The brainstorm was leeks' own teebs in miniature: speculative design written before contact. Its *invariants* aged
  well — nearly every keeper is a constraint that is cheap to state early and miserable to retrofit. Its *machinery*
  (capability tiers, the daemon, the VFS adapters) aged exactly as project-principles predicts detailed pre-contact
  plans age. The filter that worked: adopt what binds the write path, park what binds a verb that doesn't exist.
- Vocabulary drift was the main translation cost — the brainstorm's layers/effective/events are the project's
  claims/merged view/change log. The research README carries the translation table so the material stays readable.
