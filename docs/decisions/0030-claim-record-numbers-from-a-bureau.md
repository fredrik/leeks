# 0030 — Claim decision-record numbers from a bureau

Status: Decided (2026-06-14)

## Decision

A decision record claims its number when its file is created, not when it lands. `just adr-new <slug>` allocates the
next number, records it, and scaffolds the record from the template. The record of allocations — the bureau — lives in
the shared common git dir at `$GIT_COMMON_DIR/info/adr-numbers/<number>`, one file per number naming the branch and slug
that took it. Every worktree of this clone shares one common git dir, so every parallel effort sees every allocation;
the files are not in the tree, so they never appear in a diff and never merge-conflict.

The bureau is the single source of truth for allocation. `adr-new` reads it alone — `max(allocated) + 1`, never reusing
a retired number — and never consults other branches' trees. The reservation is atomic, written under `noclobber`, so
two concurrent runs cannot take the same number; the loser steps to the next. Allocation files stay for good: the bureau
is a permanent high-water mark, so landing neither releases nor reaps. The number is final from birth — filename,
heading, and every reference are correct when the record is written, and landing merges a file that already carries its
permanent name.

The one read outside the bureau is a bootstrap. When the bureau is empty — a fresh clone — the high-water mark is seeded
once from the records this checkout already holds, so a landed number is never reissued. That read touches our own tree
once, never substitutes for the bureau, and never sees another branch.

## Context

Records are written on parallel effort branches that never see each other until they land (the worktree workflow in
`CLAUDE.md`). Each branch could only pick "the next number after the highest I can see," and a branch sees only its own
base — so independent efforts grab the same number and collide at land. It happened: several live branches each claimed
0024, and one record collided with another on 0023 (now [ADR 0024](0024-a-field-colour-vocabulary.md)). A name handed
out from a global sequence by parties who cannot see each other always collides.

The fix is a single point all the efforts can see. The common git dir is exactly that: shared across worktrees, outside
the tree, already the home for cross-branch-but-uncommitted state like the land-suggestion cache. Recording each
allocation there makes the sequence global without a tracked file for branches to fight over, and names the bureau the
sole authority — no second source in the tree that can disagree with it.

## Alternatives considered

- **Scan every branch's tree for the high-water mark** — race-free and needs no bootstrap, but it makes the tree the
  authority and the bureau a cache, so a stale or rewritten branch can change what number you get. Rejected for a single
  authority: the bureau says what is allocated, and nothing else does.
- **Assign the number at land** — the number would mean "land order," race-free because landing is already serialized.
  Rejected because it drags the rename-and-rewrite of references into the riskiest moment, mid-rebase, where a reference
  may live on another branch the land cannot reach. Claiming early spends that effort once, up front.
- **A committed claims ledger or `next-number` counter** — a file in `docs/` each branch edits to reserve a number.
  Rejected: it trades a probabilistic number collision for a guaranteed merge conflict on the one line every branch
  touches. The point of the common-git-dir home is that it is never in the tree.
- **Drop numbers; identify records by slug or date** — no sequence, no collision, ever. Rejected because it discards the
  terse `ADR 0023` citation already woven through the code and docs and the at-a-glance ordering the numbers give — too
  large a reversal for a problem the bureau also solves.
- **Claim eagerly, at branch creation** — every worktree reserves a number whether or not it writes a record. Rejected
  because it burns numbers on branches that never produce one; lazy claiming at `adr-new` keeps an allocation honest.

## Consequences

The bureau is authoritative only within one clone, because leeks' parallel efforts share one filesystem and one common
git dir. Records drafted on a genuinely separate machine would not see it, and assignment would have to fall back to
land-time.

The bureau does not retroactively renumber branches that picked numbers before it existed; the in-flight 0024s are
reconciled by hand as they land. Every record born through `just adr-new` is collision-free by construction.
