# 0030 — Claim decision-record numbers from a bureau

Status: Decided (2026-06-14)

## Decision

A decision record claims its number when its file is created, not when it lands. `just adr-new <slug>` allocates the
next number, records it, and scaffolds the record from the template. The record of allocations — the bureau — lives in
the shared common git dir at `$GIT_COMMON_DIR/info/adr-numbers/<number>`, one file per number naming the branch and slug
that took it. Because every worktree of this clone shares one common git dir, every parallel effort sees every
allocation; because the files are not in the tree, they never appear in a diff and never merge-conflict.

**The bureau is the single source of truth for allocation.** `adr-new` reads it alone — `max(allocated) + 1`, never
reusing a retired number — and never consults other branches' trees. The reservation is atomic, written under
`noclobber`, so two concurrent runs cannot take the same number; the loser steps to the next. An allocation file stays
for good: the bureau is a permanent high-water mark, so landing does nothing to it and there is nothing to release or
reap. The number is final from birth — filename, heading, and every reference are correct the moment the record is
written, so landing merges a file that already carries its permanent name.

The one read outside the bureau is a bootstrap: when the bureau is empty — a fresh clone — the high-water mark is seeded
once from the records this checkout already has, so a landed number is never reissued. That reads our own tree, once,
and is never a substitute for the bureau and never sees another branch.

## Context

Records are written on parallel effort branches that never see each other until they land (the worktree workflow in
`CLAUDE.md`). Each branch's only way to pick a number was "the next one after the highest I can see" — and a branch sees
only its own base. So independent efforts grab the same number and the collision surfaces at land. It already happened:
several live branches each claimed 0024, and one record collided with another on 0023 (now
[ADR 0024](0024-a-field-colour-vocabulary.md)). A number is a name from a global sequence handed out by parties who
cannot see each other — that always collides.

The fix is a single point all the efforts *can* see. The common git dir is exactly that: shared across worktrees,
outside the tree, already the home for cross-branch-but-uncommitted state like the land-suggestion cache. Recording each
allocation there makes the sequence global without a tracked file for branches to fight over.

An earlier sketch had the allocator scan every local branch's `docs/decisions/` to find the high-water mark. It worked,
but it made the tree the authority and the bureau a mere cache — two sources that can disagree, and a tool that quietly
depends on what other branches happen to hold. Naming the bureau the sole authority is simpler and honest: a number is
allocated when it is written to the bureau, full stop. The cost is that the bureau must be seeded once on a fresh clone,
which the bootstrap read handles.

The cost of the whole approach is bounded and worth naming: the bureau is authoritative only within one clone. It works
because leeks' parallel efforts share one filesystem and one common git dir. Records drafted on a genuinely separate
machine would not see it, and assignment would have to fall back to land-time. That day is not today. This also does not
retroactively renumber branches that picked numbers before the bureau existed; the in-flight 0024s must be reconciled by
hand as they land. From here on, every record born through `just adr-new` is collision-free by construction.

## Alternatives considered

- **Scan every branch's tree for the high-water mark** — the first sketch. Race-free and needs no bootstrap, but it
  makes the tree the authority and the bureau a cache of it, so a stale or rewritten branch can change what number you
  get. Rejected for a single clear authority: the bureau says what is allocated, and nothing else does.
- **Assign the number at land** — let the one already-serialized step own the one thing that must be serialized; the
  number would mean "land order." Race-free for the same reason, but it drags the rename-and-rewrite of references into
  the landing — the riskiest moment, mid-rebase, where a reference may live on another branch the land cannot reach.
  Claiming early spends that effort once, up front, and leaves land dumb.
- **A committed claims ledger or `next-number` counter** — a file in `docs/` each branch edits to reserve a number. It
  trades a probabilistic number collision for a *guaranteed* merge conflict on the one line every branch touches. Moving
  the collision is not removing it; the point of the common-git-dir home is that it is never in the tree.
- **Drop numbers; identify records by slug or date** — no sequence, no allocation, no collision, ever. But it discards
  the terse `ADR 0023` citation already woven through the code and docs, and the at-a-glance ordering the numbers give.
  Too large a reversal to solve a problem the bureau also solves.
- **Claim eagerly, at branch creation** — every worktree reserves a number whether or not it writes a record. Simpler to
  trigger, but it burns numbers on branches that never produce one. Lazy claiming at `adr-new` keeps an allocation
  honest: it exists because a record is being written.
