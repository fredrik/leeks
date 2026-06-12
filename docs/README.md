# Documentation

Each kind of document has its own directory and lifecycle:

| Directory    | Contains                                                                                                                                                                                               | Lifecycle                                                  |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `decisions/` | Decision records, numbered `NNNN-short-title.md`                                                                                                                                                       | Append-only: only the status line changes after landing    |
| `design/`    | Design documents — the current source of truth                                                                                                                                                         | Living: edited in place as the design evolves              |
| `plans/`     | Implementation plans for active work, `YYYY-MM-DD-topic.md`                                                                                                                                            | Transient: moved to `archive/` when implemented            |
| `journal/`   | Session records, `YYYY-MM-DD-topic.md`                                                                                                                                                                 | Append-only log of notable events                          |
| `research/`  | Research and analysis that informs design: background studies (`research/beets/`), the record of the teebs predecessor (`research/teebs/`), the pre-contact brainstorm (`research/design-brainstorm/`) | Reference: revised when re-researched, archived when stale |
| `archive/`   | Implemented plans, superseded design docs. Placed in sub-directories (`docs/plans`, etc)                                                                                                               | Read-only history                                          |

## Conventions

- Decision records start from the template, [`decisions/0000-template.md`](decisions/0000-template.md), and are numbered
  sequentially: `0001-use-postgres.md`. State the decision, the context, and the alternatives considered.
- Every record carries a mandatory `Status:` line with the lifecycle Proposed → Decided | Declined → Deprecated |
  Superseded. The status line is the one part of a record that may be edited after it lands; the body is append-only. To
  reverse a decision, write a new record and mark the old one `Superseded by [NNNN](...)`. There is no separate index —
  the filenames are the index, and `grep '^Status' docs/decisions/*.md` surveys the statuses.
- Design docs describe what the system should be; plans describe how to get there. When a plan is done, archive it — the
  design doc is the lasting record.
- Keep design docs updated when code or design changes.
