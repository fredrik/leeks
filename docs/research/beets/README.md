# beets research

Analyses of beets produced on 2026-04-01 during the teebs design phase, from a snapshot of the beets source vendored
into the teebs repo. They document what beets is and why its model hurts — the factual basis for the design departures
in [research/teebs](../teebs/).

| File                                | What and why                                                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `autotagger-analysis.md`            | Decomposition of beets' autotagger into six extractable components, with line budgets; basis for porting the matcher     |
| `data-model-evolution-2014-2026.md` | Year-by-year history of beets' schema growth (56→92 item columns); explains how the denormalized model got that way      |
| `minimal-core-analysis.md`          | Blind static analysis of beets' core: the six-layer architecture and what a minimal clone actually needs                 |
| `plugin-inventory.md`               | Audit of ~80 beets plugins with categories, maturity, and real-world usage counts; scope reference for future extensions |
| `schema-reference.md`               | Complete reference of beets' SQLite schema — every column, type, and delimiter; needed for any beets migration tool      |
