# teebs research

The complete documentary record of teebs, leeks' predecessor. Everything in this directory was carried over from the
teebs repo; leeks' [core positions](../../design/core-positions.md) and
[project principles](../../design/project-principles.md) descend from this material. The factual research about beets
that grounds it lives in [research/beets](../beets/).

## The teebs design phase

The entire phase ran one evening — 2026-04-01, roughly 19:30 to 23:20:

| Time        | Commit  | What happened                                                                                            |
| ----------- | ------- | -------------------------------------------------------------------------------------------------------- |
| 19:38       | b817be9 | Fredrik's notes declared canonical: annoyances, design decisions, features, tech stack (committed 20:13) |
| 20:22       | c761a9b | The research workspace: beets analyses, three-agent brainstorms, syntheses                               |
| 20:41       | 8287423 | A compacted research summary (not carried over — leeks holds the full documents)                         |
| 20:41       | b85f579 | The 8-phase implementation plan and the risk assessment                                                  |
| 21:01       | 6e2f5b4 | The plan collapsed to 3 phases, before any code                                                          |
| 21:09–23:19 | …       | The implementation sprint: ~5,200 lines to a working `add`/`list`/`match`/`review`                       |

The design survived; the code was not carried into leeks. What the sprint taught — the assessment outlived the plan by
twenty minutes, risk didn't modulate pace — is distilled into leeks'
[project principles](../../design/project-principles.md).

## The method

The vision and the data model were each drafted three times by independent agents answering the same prompt (visions
one/two/three; data models v0/v1/v2). During the carry-over to leeks the triples were merged into the canonical
documents below; the raw drafts remain in teebs history at c761a9b.

## Files

**Inputs** — primary sources. Everything else in this directory derives from these. Edited only by Fredrik; the `.txt`
files are read-only for Claude.

| File                         | What and why                                                                 |
| ---------------------------- | ---------------------------------------------------------------------------- |
| `notes/annoyances.txt`       | The founding grievances: beets annoyances ANN-001…029, grouped and ranked    |
| `notes/design-decisions.txt` | The first design decisions: normalization, layers, copy-on-import, no gates  |
| `notes/features.txt`         | The feature wishlist: batching, genres/moods, source mixing, re-polling      |
| `notes/tech-decisions.txt`   | The tech stack and why: Python, SQLite, Pydantic, SQLAlchemy, Alembic, click |

**Design** — what teebs should be.

| File                       | What and why                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| `design-principles.md`     | The rhetorical bridge: each departure argued as *what beets does → what teebs does → why*         |
| `vision.md`                | Canonical product/architecture vision, merged from the three vision drafts                        |
| `data-model.md`            | Canonical schema — source layer + merged view, full DDL — merged from the three data model drafts |
| `brainstorm-data-model.md` | The ideas absorbed nowhere else: prior art, acquisition provenance, variants, attachments, labels |

**Execution** — how teebs was to be built, and what Claude thought of its chances.

| File                 | What and why                                                                                        |
| -------------------- | --------------------------------------------------------------------------------------------------- |
| `autotagger.md`      | The plan for porting beets' matcher: module structure, data-model adapters, dependencies            |
| `plan.md`            | The 8-phase implementation plan — superseded twenty minutes later                                   |
| `plan-simplified.md` | The 3-phase plan that was actually built; the source of leeks' slicing rules                        |
| `assessment.md`      | The risk read: autotagger port, structured field merging, source_values volume — all still relevant |
