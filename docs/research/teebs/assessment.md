# teebs assessment

> Carried over verbatim from teebs@b85f579 (2026-04-01). Claude's candid risk read of the teebs design at the end of the
> design phase. Companion to [plan.md](plan.md).

Claude's assessment of the project state and key risks.

## What's solid

**The vision is clear and well-motivated.** Every design decision traces back to a concrete beets pain point. This isn't
abstraction for its own sake -- it's fixing real problems that Fredrik has hit.

**The data model is well-designed.** The v2 data model with source layers is the right architecture. The entity
hierarchy (release_group -> album -> track, recording, work) maps cleanly to MusicBrainz without requiring all of it.
The nullable references are the right call -- model what you have, don't require what you don't.

**The tech stack is appropriate.** SQLite + SQLAlchemy + Pydantic + click is a solid, boring stack. No surprises,
well-documented, well-tested libraries.

**The decomposed import is a major improvement.** Separating add/match/review/ organize into independent steps with
persistent state is the single biggest UX win over beets. This alone would be worth the rewrite.

## What's hard

**The autotagger port (Phase 5) is the highest-risk work.** Beets' matching algorithm is ~565 lines of dense, well-tuned
logic involving string distance metrics, LAP solvers, and carefully chosen weights. It works well because those weights
were tuned over years of real-world use. Getting the port right matters more than getting it done fast.

**Structured field merging is an unsolved design problem.** The source layer stores artists as raw strings (file tags)
or JSON (MB), but the merged view needs normalized ArtistCreditORM rows. Phase 3 punts on this with "highest priority
source wins for artists" which is correct for v0.1 but will need real thought later.

**The source_values table will be high-volume.** 10k tracks x 3 sources x ~20 fields = 600k rows. SQLite handles this
fine for reads, but merge recomputation needs to be incremental from the start. A full-table recompute on every change
would be painful at scale.

## What I'd push back on (gently)

**18 tables might be more schema than v0.1 needs.** The full v2 data model is correct as a target, but implementing all
18 tables before there's any import logic means a lot of untested surface area. I'd suggest:

- Phase 1 implements all 18 tables (they're mostly straightforward)
- But only test the ones that Phase 2 actually writes to (tracks, albums, artists, artist_credits, genres, sources,
  source_values)
- The rest (recordings, works, release_groups, etc.) get exercised when MB matching lands in Phase 5

**ReleaseGroup / Recording / Work are premature without MB.** These entities only get populated during MusicBrainz
matching. They should exist in the schema (they're cheap) but shouldn't drive any Phase 1-4 logic.

## Risk map

| Risk                                             | Impact | Likelihood | Mitigation                                                     |
| ------------------------------------------------ | ------ | ---------- | -------------------------------------------------------------- |
| Autotagger port is subtly wrong                  | High   | Medium     | Test against known beets outputs with same inputs              |
| Merge recomputation is slow                      | Medium | Low        | Incremental merge from day one, benchmark at 10k tracks        |
| Structured field merging is harder than expected | Medium | High       | Punt to highest-priority-wins for v0.1, revisit with real data |
| Schema changes needed after real use             | Low    | High       | Alembic from day one, that's the whole point                   |
| mediafile edge cases                             | Low    | Medium     | It's battle-tested, but audio files are wild                   |
