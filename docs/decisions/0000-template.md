# NNNN — Short title

Status: Proposed (YYYY-MM-DD)

<!--
`just adr-new <slug>` copies this file and claims the next number (see ADR 0030). Every record carries a Status line; it
is the one line that may be edited after the record lands. The lifecycle:

    Proposed → Decided | Declined → Deprecated | Superseded

- Proposed (YYYY-MM-DD) — written, not yet settled.
- Decided (YYYY-MM-DD) — the decision stands.
- Declined (YYYY-MM-DD) — considered and decided against; the record stays as the reasoning.
- Deprecated (YYYY-MM-DD) — no longer applies and nothing replaced it; say why in one sentence after the date.
- Superseded by [NNNN](NNNN-title.md) (YYYY-MM-DD) — replaced by a newer record.

The date is the date of the most recent status change.

When a later record revises only one clause and the rest of this record still stands, it is not superseded. The amending
record adds a line of its own, one blank line below this Status line —
`Amended by [NNNN](NNNN-title.md) (YYYY-MM-DD): <what changed>` — so the revision is discoverable here, not only from
the record that made it. This is the one other edit the status block permits; the body stays append-only. Amend a third
time, or gut the decision, and supersede instead.

Title mood: imperative by default ("Store claims, not measurements"). Use declarative ("The library tree is for
humans") only when the record fixes the shape or purpose of a thing and an imperative would distort it.

Voice — a record, not an essay. This is a different register from the rest of the project's prose: a record's reader is
a future engineer in a hurry, not a student, and the decision is already made, so the record has nothing to prove.

- State, don't persuade. Write the decision as standing fact, present tense ("leek lists albums by default"). Don't
  argue the reader around.
- State the settled truth, not how it got there. When a decision was settled in stages, fold the settled facts in as
  present-tense truth; don't stack dated "resolved on contact" addenda. Git and the journal hold *when* each was
  decided; the record holds *what is true*. A deferral that still stands is the exception — it is a live consequence.
- Reasoning once, flat. Context is the forcing function that made a choice necessary, not the full intellectual
  history. Say what was decisive and stop.
- Alternatives are verdicts: "X — rejected because Y," a sentence or two each, not a paragraph re-staging the
  deliberation.
- No performance — no rhetorical reversal, no italics-for-drama, no teaching aside. beets scar-tissue is a flat
  one-liner or a link to a design doc, never a narrative paragraph.
- Length is a symptom. If a section runs past a paragraph or two, the cause is usually persuasion or pedagogy that
  belongs elsewhere; cut the cause, not the line count. (`adr-voice` guards this register.)
-->

## Decision

What was decided, stated plainly enough that someone could act on it without reading further. Lead with the decision —
it is what a future reader came for.

## Context

The situation that forced a choice: the problem, the constraints, what made this worth recording. Write it so the
decision above reads as the natural conclusion.

## Alternatives considered

- **The alternative** — and why it lost, in a sentence or two. Honest entries here are what make the record worth
  keeping; "we never considered anything else" is also an honest entry.

## Consequences

Optional — include it when the decision creates something a future reader would be surprised by: a new constraint, an
obligation or follow-on work, or a deferral that still stands ("the JSON envelope's shape is decided when that slice
arrives"). Omit it when the decision is self-contained; do not pad it with "none". This is what the decision *costs or
commits*, not why it was chosen (Context) or the roads not taken (Alternatives).
