# leeks — design notes

> Output of a design brainstorm, 2026-06-10 — written against an empty repository, before any implementation contact.
> Preserved as research; see the [README](README.md) for the disposition of every idea. Decisions are tagged
> **[settled]** (decided before/during this session), **[leaning]** (strong direction, not committed), or **[open]**.
> Companion documents: [storage-backend.md](storage-backend.md), [actors-capabilities.md](actors-capabilities.md) (both
> never adopted; their ADR numbering predates `docs/decisions/`).

## 1. What leeks is

A music library organiser and spiritual successor to beets, built around albums rather than files. Layered metadata
sources, a normalised relational schema, full history of every change — git for your music library's metadata.

The beets failure modes it exists to fix:

1. Imports gate on match confidence; uncertain files sit in limbo outside the library.
2. Wrong matches are hard to undo; sources overwrite each other (`mbsync` clobbers edits).
3. The schema is denormalised and file-centric; album-level edits don't propagate to tracks.

## 2. Core model: three primitives **[settled]**

1. **Layers** — each source's view of an entity (file tags, MusicBrainz, Discogs, tracker folder name, Last.fm
   scrobbles, user edits, agent output). Immutable per fetch, timestamped, with provenance.
2. **Effective metadata** — deterministic merge of layers by precedence policy, per-field overridable. Computed, never
   hand-written.
3. **Projections** — everything derived: file tags, directory trees, VFS views, playlists, exports. Always
   re-renderable, never canonical.

Key consequences:

- **User edits are a layer** (`source=user`, highest precedence). Refetching a source can never clobber an edit; undo =
  supersede a user-layer entry.
- **Original file tags are layer 0**, preserved forever.
- **Per-field provenance is native** (`leek blame`).
- Only `user`-wins is fixed; layer precedence relative to external sources is per-field configuration **\[open: config
  shape\]**.

### Medallion mapping

The primitives are bronze/silver/gold, and the discipline transfers:

```
bronze  ↔ layers       immutable, append-only, per-source (even user edits enter here)
silver  ↔ effective    derived canon — a pure function of (layers, precedence config)
gold    ↔ projections  consumption-shaped, regenerable
```

Hard rules that follow:

- `leek dump` serialises **bronze + events, never effective**; effective is recomputed on load.
- Layer payloads keep the **raw source response** (possibly compressed / two-tier) — a cache is disposable, bronze is
  not. Enables re-extraction of new fields without re-fetching.
- Effective metadata is a **materialised, rebuildable index** (`leek rebuild` ≈ `dbt run`); recompute incrementally per
  entity whose layers changed. Corruption of effective is an inconvenience; corruption of layers is data loss.
- The staging/review flow is the **WAP pattern** (write–audit–publish).
- Do not import medallion ceremony (tier naming, module structure) — only the invariant.

## 3. Schema sketch **[leaning]**

```
artist ─ artist_credit ─ release_group ─< release ─< medium ─< track
                                            │                    │
                                        attachment          track_file
layer(entity_type, entity_id, source, fetched_at, data, payload_hash)
event(id ULID, ts, actor, action, ref)
```

- `release` carries label, catno, barcode, country, date — pressing identity is first-class. Tracker folder names
  (`{Label - CATNO}`) are parsed by a source layer, not treated as decoration.
- `track_file` attaches an audio file to a track *slot*: a release with zero files is a native wantlist entry; a track
  may have multiple files (FLAC + V0 copy).
- `attachment` holds .log/.cue/artwork/.nfo at release level.
- Tracks join to album-level fields rather than duplicating them — edit propagation is a non-feature by construction.
- ULIDs for event ids: time-sortable, prefix-addressable like git SHAs.

## 4. Import pipeline: ingest ≠ identify **[settled]**

```sh
leek add ~/incoming/**   # fast, dumb: hash, read tags (layer 0), register. Never blocks.
leek match               # batch: propose candidates; auto-accept above threshold → staging
leek review              # interactive triage, resumable, sorted by confidence
```

Every file is in the library from second one, queryable as `state:unidentified`. Matching is in-process (jellyfish
string distance + lap linear assignment over duration/title matrices, numpy). Candidate ideas: AcoustID fingerprints as
file *identity* (dedupe across encodes, survive retags) **[leaning]**.

## 5. History and the git porcelain **[leaning]**

```
leek log [query]                  # event history; --actor filter; --follow across re-matches
leek show <ref|query>             # canonical rendering of a release or event
leek diff                         # staged proposals vs effective — what `apply` would do
leek diff @2026-01-01 @now [q]    # what changed since
leek diff --layers mb discogs [q] # source-disagreement report (curation tool)
leek blame [query]                # per-field provenance
leek apply / leek reject          # accept / refuse staged proposals
leek revert <event>               # compensating event — history is append-only, no `reset`
leek edit [query]                 # $EDITOR on canonical YAML; saved diff → user layer
```

- `revert` is **forward motion** (append a compensating event). History is never rewritten — this keeps `@date` time
  references sound forever.
- `leek edit` is `kubectl edit` for albums, including multi-doc YAML for bulk.

## 6. Canonical serialisation **[open — ADR 0002, highest-priority spec]**

One deterministic, stable-ordered text rendering (YAML or TOML) of a release's effective metadata. It is consumed by:

1. `leek dump` / `leek load` (interchange — at bronze level, see §2)
2. `leek diff` (unified diffs of renderings; pipes into `delta`)
3. `leek show` / `leek edit` ($EDITOR round-trip → user-layer edits)
4. the VFS `.release.yaml` sidecar (read, later writable)
5. proposal payloads in the actors API (ADR 0003)

Spec must cover: field ordering, determinism/round-trip guarantees, provenance representation (likely effective-only
with optional provenance comments), versioning of the format as a compatibility surface, and the bronze-vs-effective
distinction between dump and show/edit renderings.

## 7. Virtual filesystem **[leaning]**

The browse tree is a render *function*, not a render artifact: a query result with a POSIX API.

### Views

Top-level dirs as `(query, path_template)` pairs in config:

```
/library/
  by-artist/…/Album (Year)/01 - ….flac
  by-label/Warp/WARP55 - …/
  wantlist/                                  # releases with zero files
  query/genre:idm/year:2003/label:warp/      # path segments compose as AND
  playlists/unplayed-2020s.m3u
  @2026-01-01/by-artist/…                    # time travel: effective-as-of
```

- `query/` uses the synthetic-FS trick: `readdir` lists curated entries (saved + recent queries), `lookup()` accepts
  anything.
- Faceted refinement: readdir of a partial query may list suggested next atoms.
- Synthesized per-album files: `cover.jpg` (from attachments), optional `album.nfo`, `.release.yaml` sidecar,
  `.provenance.json`.
- m3u playlists use mount-relative paths. Two kinds: **live** (query-defined, regenerated on read) and **pinned**
  (materialised, user-ordered, stored in user layer); `cp live/x.m3u pinned/` freezes one.
- Scrobble-layer queries make rediscovery playlists trivial (`playcount:>10 lastplayed:<2025-06`).

### Read modes (per view)

1. **passthrough** — proxy canonical bytes (FUSE passthrough mode, Linux ≥6.9).
2. **retag** — serve files with *effective* tags spliced over layer-0 tags at open time. Canonical bytes untouched →
   torrents keep seeding; every other consumer sees corrected metadata. FLAC is tractable (front-loaded metadata blocks;
   deterministic synthesized size so `getattr` is honest). **\[open: prototype this first — highest leverage, highest
   risk\]**
3. **transcode** — ffmpegfs-style derived views (e.g. `/library/v0/`); size estimation is the known pain; defer.

### Write semantics ladder

- v1: read-only.
- v2: rename-as-edit — `mv` parsed against the view template → user-layer edit.
- v2: writable `.release.yaml` sidecar — `:w` → parse → Pydantic validation → user-layer edit; failed validation rejects
  the write. This makes every editor a leeks frontend with full history.
- research toy: intercepting binary tag writes from arbitrary apps (fragile; the YAML sidecar is the sane version).

### Architecture

Transport-agnostic core with thin adapters:

```
VirtualTree:  resolve(path) -> Entry | readdir(Entry) -> [Entry] | open(Entry) -> Reader
adapters:     FUSE (pyfuse3) | NFS serve | WebDAV serve
```

- macOS: avoid macFUSE kext pain — FUSE-T or `leek serve nfs` + loopback mount.
- Kubernetes/Talos: NFS/WebDAV daemon is an unprivileged pod; FUSE needs /dev/fuse + caps.
- Invalidation: library generation counter — `PRAGMA data_version` (SQLite) / `LISTEN/NOTIFY` (Postgres) behind one
  interface. inotify does not propagate through FUSE; assume consumers poll (nudge mtimes for Navidrome-style scanners).
- Stable inodes per (view, entity) via persisted inode table (rsync correctness).
- Cache negative lookups (scanners hammer cover.jpg/.nfo probes).
- Path sanitisation + collision disambiguation (auto-suffix `[catno]`) live in the template engine, shared with
  `leek export`.
- Prior art to mine for scars: mp3fs/ffmpegfs (size estimation), rclone VFS caching, beetfs (existence unverified —
  check).

`leek render` (hardlink tree) demotes to an escape hatch for daemon-less contexts; `leek export --to … --transcode …`
survives for copies-with-written-tags.

## 8. Query language **[leaning]**

beets-style atoms (`field:value`, ranges) compiled to SQL over the normalised schema via SQLAlchemy Core. Ship read-only
views (`v_track_effective`, `v_release_effective`) so DuckDB / dbt / Datasette can attach — the library is an analytics
target (scrobble layer included) on either backend.

## 9. Storage (ADR 0001, Proposed) — summary

- **SQLite default and reference backend** (WAL, STRICT, foreign_keys=ON). Local-first is the product; quickstart never
  mentions anything else.
- **Postgres supported**, selected by URL (`LEEKS_DB=…`, psycopg 3). Trigger is topology, not scale: DB and clients on
  different hosts (SQLite over NFS/SMB is unsafe). The reference deployment is already multi-host.
- **Portability enforced by CI matrix on both engines from the first migration**, plus a discipline list (Core
  constructs only; join tables not ARRAY; SQLA JSON type only; UTC TypeDecorator datetimes; batch_alter_table; matching
  stays in-process; notification behind one interface).
- **`leek dump | leek load` is the canonical interchange** and backend migration path. The DB is a rebuildable index of
  the dump.

## 10. Actors and capabilities (ADR 0003, Proposed) — summary

Single-person, **multi-actor**: human, cron, pipelines, AI agents.

- Actor identity on every write (`user`, `cron:<name>`, `agent:<name>`).
- **One write path** through leeks core; direct DB writes unsupported. Daemon-mediated access is the plan of record.
- Automated actors write **their own layers**, default precedence below `user` → automation can't clobber edits; rogue
  actors are contained by dropping a layer and/or revoking a capability.
- Capability tiers: `read` → `propose` → `write-own-layer` → `apply`. Agents default to `propose`; auto-apply only by
  explicit actor+threshold policy. Proposals are PRs against the library (WAP).
- Idempotency: content-hashed layer payloads; identical re-writes are no-ops.
- Optimistic concurrency: per-entity revision; `apply` is compare-and-swap.
- Contents ops (move/transcode/export/art) are journaled events; long-running ones are tasks (enqueue with `propose`,
  execute with `apply`).
- **MCP is the canonical agent surface**: `query`, `show`, `log`, `propose_edits`, `apply`, capability-gated.
- Consequence: `leek review` must scale to bulk ("agent proposed 400 genre edits") — review-by-actor and bulk accept are
  requirements.

## 11. Plugin surface **[leaning]**

One extension protocol first; resist hook soup:

```python
class MetadataSource(Protocol):
    name: str
    def candidates(self, release: ReleaseInfo) -> list[CandidateInfo]: ...
    def fetch(self, ids: list[str]) -> LayerData: ...
```

MusicBrainz, Discogs, Last.fm, AcoustID, tracker-folder parser all fit it. Path formats, dedupe, integrity stay core.
Lifecycle hooks later, if ever.

## 12. Stack **[settled]**

Python ≥3.14, uv, hatchling, click, SQLAlchemy 2.0, Alembic, Pydantic v2 (pipeline models `TrackInfo`/`AlbumInfo` as
lingua franca; ORM for persistence only), mediafile, jellyfish + lap + numpy, musicbrainzngs, pydantic-settings,
platformdirs, rich; ruff, ty, pytest (+ testcontainers for the Postgres matrix).

## 13. Open questions / next steps

1. **ADR 0002: canonical serialisation spec** — most load-bearing decision left; five consumers (§6).
2. **Retag-on-read FLAC spike** — ~50 lines: synthesize VORBIS_COMMENT, splice frames, verify with mpv + hex editor.
   Determines whether the VFS ships retag mode or passthrough-only at v1.
3. **Layer precedence configuration shape** — per-field rules, defaults, where agent/cron layers sit relative to
   external sources.
4. **Capability/token mechanics + MCP tool schema** — implementation spec.
5. **Review UX for bulk proposals** — filter by actor, confidence bands, bulk accept/reject.
6. **Dump format vs raw-payload archival** — how layer raw responses are stored, compressed, pruned.
7. ADR statuses: 0001 and 0003 are Proposed; acceptance is the maintainer's call, in the repo, not in a chat.
