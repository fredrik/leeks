# Carrying teebs into leeks

Session record, 2026-06-10 to 2026-06-11. The complete documentary record of teebs — leeks' predecessor — was examined
commit by commit and carried into `docs/`, ending with leeks' first process document distilled from what the teebs build
taught.

## The commits

| Commit  | What                                                                                   |
| ------- | -------------------------------------------------------------------------------------- |
| 27b8f20 | Founding notes (annoyances, design/tech decisions, features) from teebs@b817be9        |
| 86be103 | The research workspace from teebs@c761a9b: beets analyses, canonical merges, syntheses |
| 70d5455 | Two over-trimmed brainstorm seeds restored (attachments beyond cover art, user labels) |
| 7aa691f | The 8-phase plan and risk assessment from teebs@b85f579                                |
| 120343c | Project principles distilled from the plan simplification (teebs@6e2f5b4)              |
| 7fdb277 | Founding notes moved into `docs/research/teebs/notes/`; the teebs README written       |
| e5007fe | README linked to the teebs repo                                                        |
| 80d23c0 | Founding notes converted from `.txt` to markdown, on Fredrik's request                 |
| acfd44b | CLAUDE.md tightened after an evaluation pass                                           |

## Method

- Every teebs commit was analyzed before deciding disposition: carry verbatim, synthesize, or skip with a reason.
- The triples — three independent same-prompt drafts of the data model (v0/v1/v2) and the vision (one/two/three) — were
  merged into canonical documents by parallel agents. The subsumption hypothesis (v2 ⊃ v1 ⊃ v0) held, but the siblings
  contributed real material: v2 lacked the entire Pydantic layer, vision-three lacked the decisions table.
- The merge surfaced a conflict no single draft contained: `external_ids` (merged view) vs `source_matches` (source
  layer) record overlapping facts. Now an open question in `data-model.md`.
- teebs' compacted research summary (teebs@8287423) was used as a completeness check against the trimmed brainstorm — it
  caught two orphaned ideas — and was itself not carried over, being a lossy copy of documents leeks holds in full.

## Deliberately not carried over

The raw triple drafts (superseded by the canonical merges, preserved in teebs history), the teebs workspace CLAUDE.md,
`plugins.analysed` (raw data behind the plugin inventory), and the research summary.

## Lessons, recorded in [project-principles](../design/project-principles.md)

The teebs implementation sprint (~5,200 lines, one evening) taught the two lessons the principles now encode: the risk
assessment outlived the detailed plan by twenty minutes, and risk didn't modulate pace — the highest-risk work (the
autotagger port) landed at plumbing speed with nothing in place to notice if it was wrong. The plan simplification's
moves became leeks' slicing rules, with one adaptation: leeks defers the source-layer *machinery*, never the layering
itself, which is a core position.

## Left open

- The roadmap in `docs/plans` — the first document to be written under the new project principles.
- CLAUDE.md knowingly states two things that are not yet true (CI running `just check`; TrackInfo/AlbumInfo and the
  `leek` entry point existing). Both become true with the first code slices; ignored until then.
