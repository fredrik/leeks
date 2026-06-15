# Project principles

How leeks is planned and built. [Core positions](core-positions.md) constrain what the system is; this document
constrains how we get there.

These rules are distilled from the teebs build — specifically from the
[plan simplification](../research/teebs/plan-simplified.md) that collapsed an 8-phase plan to 3 phases twenty minutes
after it was written, and from what the [assessment](../research/teebs/assessment.md) predicted correctly that the
sprint then ignored.

## Planning model

**A thin roadmap orders the slices.** One document stating sequence and intent — never per-slice deliverable lists.
Detailed plans written ahead of contact decay in minutes; the teebs plan proved it.

**One plan per slice, written just in time.** A slice plan is written when the slice starts, is small enough to
implement and verify in one session, and is archived when implemented. Never plan more than one slice ahead in detail.

**Verification comes first in the plan.** A slice plan states how the work will be verified before it states what gets
built. New behaviour requires new tests; risky behaviour requires a harness.

**Rationale outlives its plan.** Plans get archived; the rationale that must survive lives in a design doc, or — for the
few decisions weighty enough that reversing one unknowingly would cause harm — a record in
[docs/decisions](../decisions/). Most design choices are not records; the test is in CLAUDE.md.

**teebs is precedent, not blueprint.** The teebs record ([docs/research/teebs](../research/teebs/)) preserves
*decisions* and their reasons — the source layer, import-everything, non-destructive defaults. Its schemas, models, and
plans were speculative maximalist noodling written before contact with implementation, and they anchor: slice 1's detail
plan inherited a credits table from the teebs data model that carried no information (ADR 0009), and the parity-twin
experiment could not catch it because both twins read the same plan. Design every component from local information — the
data this slice actually has — then consult teebs for the scar tissue, never the table layouts.

## Slicing rules

**Slice by data availability.** Infrastructure arrives with the data that justifies it: the merge machinery arrives with
the second metadata source, the MusicBrainz entities arrive with the matching that populates them. Phase boundaries
follow what data exists, not design completeness.

**Layering from day one; machinery deferred.** "Sources are layers" is a core position, so the write path goes through
the source layer from the first slice — file tags write through `source_values` even while file tags are the only source
and merging is identity. What waits for a second source is the machinery: merge strategies, confidence handling, the
pending-changes queue, review. The write-path discipline is the part that is hard to retrofit; the cleverness is not.

**Undecided components are excluded.** An open design question disqualifies a component from the current slice. Nothing
gets built while its usage policy is unsettled — teebs cut flex_attrs from the build for exactly this reason.

**Open questions carry punts.** Every open question gets an explicit interim answer ("highest-priority source wins for
artists, for now") so implementation never stalls on one. The punt is recorded next to the question.

**Every slice ends runnable.** Each slice produces something that runs against a real library and can be inspected — get
to `add` then `list`/`info` before anything clever, and dogfood from the first slice.

**Risk leads with verification.** The riskiest work in a slice is planned around its harness, built first. The matcher
port starts with a beets-parity harness (fixture inputs, beets' known outputs, the port must reproduce them) before any
porting. In teebs, the highest-risk work landed at the same pace as the plumbing and nothing would have noticed if it
was wrong; the harness is what notices.

## Ethos and pathos

Newer than the teebs lessons above — added as the build itself began. The first is ethos, character: how we work. The
second is pathos, feeling: what working on leeks should feel like.

**All work happens on a feature branch in its own worktree.** The main checkout is never edited directly, and main's
history is semi-linear — branches rebase onto main, then land with a single `--no-ff` merge marker: an imperative title,
plus a label when there is something to cite — `Add CLI skeleton (Slice 0)`. The first-parent history stays linear and
reads like the roadmap. A branch waits unmerged until Fredrik integrates it.

**leeks is a thrill and a joy to work with.** Joy is a requirement, not a garnish. The CLI earns it with output worth
reading and help worth asking for; the project earns it with fast feedback loops and code that is a pleasure to change.
When something about leeks feels like a chore, treat it as a bug.
