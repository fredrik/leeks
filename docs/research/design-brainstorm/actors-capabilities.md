# ADR 0003: Actors, capabilities, and the write path

- **Status:** Never adopted — preserved as research. The ADR numbering predates `docs/decisions/` and collides with it;
  see the [README](README.md) for what was distilled and where.
- **Date:** 2026-06-10
- **Relates to:** [storage-backend.md](storage-backend.md) (same provenance); a canonical-serialisation spec that was
  never written

## Context

leeks is a single-person, multi-actor system. One human owns the library, but it is queried and mutated concurrently by
several kinds of actor, possibly from different hosts:

- the human, via CLI, `$EDITOR`, and writable VFS surfaces
- cron jobs (scrobble sync, ingest pipelines, integrity checks)
- AI agents, primarily as MCP clients, enriching metadata and operating on contents

The layered metadata model and append-only event log are core promises: every effective value has provenance, every
change has history. Both promises are fiction the moment any actor writes the database directly.

Automated actors also introduce failure modes humans don't: they re-run, they race each other, and they can be wrong at
scale.

## Decision

1. **Actor identity is first-class.** Every event and every layer write carries an actor: `user`, `cron:<name>`,
   `agent:<name>`, `pipeline:<name>`. There are no anonymous writes. `leek log --actor` and `leek blame` are the audit
   surface.

2. **There is exactly one write path.** All mutations go through leeks core — the same code whether invoked from the
   Python API, the CLI, or the daemon. Direct database writes are unsupported. The daemon-mediated access model deferred
   in ADR 0001 is hereby promoted to the plan of record.

3. **Automated actors write to their own layers.** An agent's or job's contributions live under its own source
   (`agent:genre-tagger`, `cron:lastfm-sync`) with precedence below `user` by default; ordering relative to external
   sources is per-field configuration. Consequences by construction:

   - automation can never clobber a human edit;
   - a misbehaving actor's entire contribution can be dropped by removing its layer — effective metadata recomputes,
     nothing else is touched.

4. **Four capability tiers**, granted per actor:

   | capability        | grants                                           |
   | ----------------- | ------------------------------------------------ |
   | `read`            | query, show, log, blame, diff                    |
   | `propose`         | write to staging only                            |
   | `write-own-layer` | append to the actor's own source layer           |
   | `apply`           | accept staged proposals; execute file operations |

   Agents default to `propose`. Auto-apply happens only by explicit policy (actor + confidence threshold), never
   implicitly.

5. **Staging is the review mechanism for all actors.** Agent and pipeline proposals appear in `leek review` alongside
   match candidates, filterable and bulk-acceptable by actor. Proposals are pull requests against the library.

6. **Writes are idempotent.** Layer payloads are content-hashed; a re-run that would write an identical payload is a
   no-op. Cron jobs may be re-executed freely.

7. **Applies use optimistic concurrency.** Each entity carries a revision; `apply` is a compare-and-swap against the
   revision the proposal was staged on. On conflict the apply fails and the actor re-proposes against current state —
   the `git push` rejection, per release.

8. **Contents operations are journaled.** File moves, exports, transcodes, and art fetches are events like any other.
   Long-running operations are tasks: any actor with `propose` may enqueue, execution requires `apply`.

9. **MCP is the canonical agent surface.** The daemon exposes tools mapping onto core verbs — `query`, `show`, `log`,
   `propose_edits`, `apply` — gated by the capability tier of the connecting client. Proposal payloads use the canonical
   serialisation (ADR 0002).

## Alternatives considered

- **Direct DB access for trusted jobs.** Fast and tempting; destroys provenance and bypasses every invariant. Rejected
  unconditionally.
- **A single shared `automation` actor.** Simpler config, but no blast-radius isolation and no per-actor audit.
  Rejected.
- **Full RBAC/ACLs.** Overkill for a single-person system; four tiers cover every real scenario without an authorization
  framework.
- **Pessimistic locking.** Unnecessary at this contention level; CAS on apply is sufficient and keeps actors lock-free.
- **Agents writing file tags or files directly.** Violates DB-is-canon; rejected. Files remain projections regardless of
  who is acting.

## Consequences

**Positive.** Rogue automation is contained twice over: revoke the capability, drop the layer. The audit trail covers
machines and humans with the same machinery. Agents are safe by default — `propose` costs nothing and risks nothing.
Human and machine writes share one set of invariants, so there is no privileged code path to drift.

**Costs.** The core library API becomes a stability surface earlier than v1. Capability grants need a configuration
story (per-client daemon config or tokens — implementation detail, not ADR material). The review UX must scale from "a
handful of match candidates" to "an agent proposed 400 genre edits" — review-by-actor and bulk operations are now
requirements, not nice-to-haves.

**Neutral.** Precedence of automated layers relative to external sources (MusicBrainz, Discogs, tracker metadata) is
deliberately left to per-field configuration; only `user`-wins is fixed.

## Follow-up

- ADR 0002 (canonical serialisation) gains a consumer: proposal payloads.
- MCP tool schema and capability/token mechanics go in an implementation spec, not an ADR.
- ADR 0001 amended: context now records the multi-actor reality, and the daemon-mediated alternative is marked as
  adopted here.
