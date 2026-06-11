# Documentation

Each kind of document has its own directory and lifecycle:

| Directory   | Contains                                                                                                                                   | Lifecycle                                                  |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `adr/`      | Decision records, numbered `NNNN-short-title.md`                                                                                           | Append-only: never edited, superseded by a new record      |
| `design/`   | Design documents — the current source of truth                                                                                             | Living: edited in place as the design evolves              |
| `plans/`    | Implementation plans for active work                                                                                                       | Transient: moved to `archive/` when implemented            |
| `journal/`  | Session records, `YYYY-MM-DD-topic.md`                                                                                                     | Append-only log of notable events                          |
| `research/` | Research and analysis that informs design: background studies (`research/beets/`), the record of the teebs predecessor (`research/teebs/`) | Reference: revised when re-researched, archived when stale |
| `archive/`  | Implemented plans, superseded design docs. Placed in sub-directories (`docs/plans`, etc)                                                   | Read-only history                                          |

## Conventions

- ADRs are numbered sequentially: `0001-use-postgres.md`. State the decision, the context, and the alternatives
  considered. To reverse a decision, write a new record that supersedes the old.
- Design docs describe what the system should be; plans describe how to get there. When a plan is done, archive it — the
  design doc is the lasting record.
- Keep design docs updated when code or design changes.
