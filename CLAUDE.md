# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

leeks is a music library organiser and spiritual successor to beets.

## Design principles

Keep it simple.

Don't add when you can delete.

## Documentation

Documentation is kept in the `docs` directory:
`docs/adr`: proper ADR-style decision records. Official.
`docs/archive`: where outdate documentation and implemented plans are archived.
`docs/design`: design documents. should have a long expected lifetime.
`docs/journal`: date-stamped filenames that record specific sessions.
`docs/plans`: where active plans live.

Claude should religiously use `docs` to document design decisions and other notable events.

Claude should keep existing documentation updated when code, design, etc is changed.

Claude should archive outdated documentation and plans that are already implemented.

## Spec-driven development

This project follows a spec-driven approach. The human coder is steering spec and plan, the agent is implementing.

We use [OpenSpec](https://github.com/Fission-AI/OpenSpec) to manage changes. Change artifacts (proposal, design, tasks) and specs live in the `openspec` directory. The workflow is driven by the `/opsx:*` commands: `explore`, `propose`, `apply`, `sync`, `archive`. OpenSpec changes are the working plans; `docs/adr` remains the home for durable decisions that outlive a change.


## Local harness

Claude should strive to use an efficient local test harness to run and verify the code. The feedback loop should be as tight as possible. Insist on improving the tooling if deemed less than perfect.

## Tooling

The project uses Python and uv.

## Code

Remove dead code.
