# Raw source capture — the input each source read

A design + slice plan. Date: 2026-06-15. Status: proposed, not yet sliced into the roadmap.

## The problem

leeks has two sources today: `file_tags` (reads audio tags via mediafile) and `path` (parses the album's directory
name). Both keep only their *interpreted claims* in `source_values`. The raw input each source read its claims from is
thrown away:

- `file_tags` maps a curated handful of frames/atoms to claim fields (`title`, `artist`, `album`, `year`, `genres`,
  `track`, `tracktotal`) and discards every other tag the file carries.
- `path` parses the directory *basename* (`directory.name`) and keeps nothing of the path it parsed — and the per-file
  original location survives only incidentally, as the absolute `files.source_path`.

The cost: a claim is not auditable back to its input (you cannot ask "what did the tags actually say?"), data we do not
yet map is lost on import (re-deriving it means re-reading the original, which `add` does not retain), and the path's
locational provenance is an absolute machine path — not portable, and the wrong grain for a multi-disc layout.

This plan names the concept that fixes all three, fits it into the claims/measurements split (ADR 0007), and slices the
work.

## The concept: source input

I propose one term of art — **source input** — for *the raw thing a source read, preserved verbatim, before any
interpretation*. It is a third category beside **claim** and **measurement**, and the cleanest way to see why is the
two-test framing ADR 0007 already uses.

- A **measurement** is a fact about bytes, locally recomputable, *with no room for disagreement* — and not the property
  of any source. Bitrate is a measurement.
- A **claim** is an *interpretation* a source asserts and another source can disagree with. `artist = "Daft Punk"` is a
  claim, whoever made it.
- A **source input** is neither. It is not recomputable from the library's own bytes (the original may be gone; the
  add-relative directory is a fact about *where the import came from*, not about the copied bytes), and it asserts
  nothing on its own — `TPE1 = "Daft Punk"` is data the *file states*, but turning that frame into the `artist` claim is
  the `file_tags` source's interpretation. The input is the substrate; the claim is the reading.

The discriminator that resolves the borderline ADR 0007 worries about ("tags are read from bytes, yet are assertions"):
a source input is **attributable to a source and preserved for audit, but carries no merge semantics**. No merge rule,
no confidence, no precedence ever reads it. That is exactly what claims and measurements both *do* have (claims merge by
priority; measurements are recomputed and always-win-by-being-fact). Source input sits underneath both: it is what a
source looked at, kept so its claims can be checked and re-derived, and so unmapped data is not lost.

Two concrete inputs, both **file-level** (they attach to the `File` row, alongside `source_path` and the measurements):

1. **Raw tags** — the complete native tag set of each file (every frame/atom, not just the mapped fields). The input the
   `file_tags` source read.
2. **Source directory** — the directory each file came from, *relative to the parent of the `add` argument*. The
   locational input the `path` source's album-level claims are derived from.

The glossary gains **source input** in the same change, defined as above and cross-referenced from **claim** and
**measurement**.

### Why one concept, not two columns

Tags and the relative directory look unrelated — a blob of frames versus a short path string. But they answer the same
question for two different sources: *what did this source actually read?* Framing them as one concept (source input) is
what lets a future source — MusicBrainz's raw JSON response is the obvious next instance — slot in without inventing a
third storage idea each time. It also keeps the audit story uniform: `leek show` (or the review queue) can one day say
"the `file_tags` source read these tags and claimed this; the `path` source read this directory and claimed that."

It does *not* mean one table. The two inputs have different shapes (a multi-valued key/value set vs a single string),
and forcing them into one row would be the kind of false uniformity ADR 0007 rejects. One concept, shaped storage per
input — see the schema.

## Relationship to the existing model

| Layer            | Question                     | Home                        | Merge?                 |
| ---------------- | ---------------------------- | --------------------------- | ---------------------- |
| Measurement      | What are the bytes?          | columns on `files`          | n/a (recomputed)       |
| **Source input** | What did the source read?    | `files` (file-level inputs) | **no**                 |
| Claim            | What does the source assert? | `source_values`             | by priority (ADR 0031) |
| Merged view      | What is effective?           | albums/tracks/...           | computed               |

Source input is the layer the claim layer rests on. The album-level path claims (`artist`/`title`/`year`/`medium`/...)
are derived from the **common root component** shared by all an album's files — a single album-level parse of one
directory basename. The raw capture is **per-file** (one source directory per `File`). These are not the same grain and
the plan keeps that explicit: the claims are album-level interpretations; the per-file source directory is the verbatim
locational input, retained per file so a multi-disc layout (`CD1`/`CD2`) is not flattened. The album-level parse
continues to read `directory.name` exactly as it does today; capturing the per-file directory does not change it.

## Schema

### Raw tags — a normalised table, native keys verbatim

```
class FileTagRaw(Base):
    __tablename__ = "file_tags_raw"
    id: int  (pk)
    file_id: int  (fk files.id, indexed)
    key: str        # native, format-specific: "TPE1", "ARTIST", "©ART"
    value: str      # the frame/atom value, verbatim
    ordinal: int    # 0-based position within a repeated key, for multi-value tags
    # UniqueConstraint(file_id, key, ordinal)
```

Decisions baked in:

- **Native keys, verbatim, un-normalised.** A Vorbis `ARTIST`, an ID3 `TPE1`, and an MP4 `©ART` are stored under their
  own format-native key. Normalising them to a common vocabulary would be interpretation — exactly the work that
  produces a *claim* — and would lose the very thing raw capture exists to keep: what the file literally said. "Store
  verbatim" is normative (glossary; ADR 0008); raw capture is the verbatim layer par excellence. The file's `format`
  column already records which key namespace applies, so no separate namespace column is needed.
- **A normalised table, not a JSON blob.** Weighed below; chosen for queryability (a future "find files with a
  `MUSICBRAINZ_TRACKID`" query is a `WHERE key = …`, not a JSON scan), for honoring portability.md's preference
  (junction tables over engine-specific shapes; JSON columns are allowed but earn no advantage here), and because
  multi-valued tags want first-class `ordinal` rows rather than nested arrays.
- **`ordinal` preserves multi-value order.** ID3v2.4 multi-value frames, repeated Vorbis comments, and MP4 list atoms
  are all ordered; the ordinal keeps that order without making the value a delimited string.

Alternatives weighed:

- **JSON column `files.raw_tags`** (`dict[str, list[str]]`). Simpler — one column, no table, no join. But it buries the
  data behind JSON operators (portability.md bars engine-specific JSON operators in core paths, so any query degrades to
  load-and-scan in Python), and it makes the multi-value ordering implicit. The normalised table is barely more code and
  far more honest. Rejected, but it is the fallback if the table proves heavy in practice.
- **Normalised keys** (map every format's artist frame to a canonical `artist`). Rejected: that is claim-making, and we
  already do it — in `tags.read_tags`. Raw capture must stay below that line.

### Source directory — a column on `files`

```
class File(Base):
    ...
    source_dir: Mapped[str]   # the add-relative parent directory; see the rule
```

The rule (from the goal, confirmed): the file's parent directory, **relative to the parent of the directory passed to
`leek add`**. This retains the add-argument's own basename (portable, identifies the release) and drops the absolute
machine prefix. Per file, so a multi-disc layout keeps its `CD1`/`CD2`.

Example: `leek add ~/downloads/Empires-Often_Enough-2026`; the file
`~/downloads/Empires-Often_Enough-2026/CD2/03-ding.flac` stores `source_dir = "Empires-Often_Enough-2026/CD2"`. A flat
album reduces to a single component: `"Artist - Album (2001)"`.

Decisions:

- **Store the directory, not the full file path.** The example stores the dirname; the filename is already implied by
  `files.path` (the destination filename) and is not provenance the path source reads. Storing the directory only
  matches the example and avoids a redundant filename.
- **Grain is `File`, not `Track`.** Provenance is about *this byte-set's origin*; two files realising one track can come
  from different directories (a multi-disc track split, or a re-add). The `File` row already holds `source_path` and the
  measurements — `source_dir` belongs in exactly that company.
- **A plain column, not a table.** It is one single-valued string per file. No arity, no namespace, no ordering — a
  column is the simple right answer.

## Reconciling with `files.source_path`

`source_path` holds the **absolute** original path and is matched by `_refuse_readds` to reject re-adds. `source_dir` is
`source_path` minus the absolute prefix minus the filename. They overlap but are not redundant, and the plan keeps
**both**, each doing one job:

- `source_path` stays the **re-add guard**. Its absolute, machine-specific exactness is the feature: re-adding the *same
  file from the same place* is refused; the *same album fetched again to a different download dir* is a legitimately new
  import and should not be silently blocked. Switching the guard to relative matching would change that cross-location
  behaviour — quietly, and for the worse — so the guard stays absolute. (This is recorded as the re-add punt; this plan
  does not reopen it.)
- `source_dir` is the **portable locational input** the path source read — kept for audit and re-derivation, never
  consulted by the re-add guard.

No duplication of *provenance* results: `source_path` is "exactly where this file was, for refusal"; `source_dir` is
"the relative shape of where it came from, for the path source's audit." If anything, having both makes the relationship
legible — `source_dir` is derivable from `source_path` and the add argument at capture time, and we store it rather than
re-derive it because the add argument is not retained after import.

## Pipeline placement

Both captures happen at **copy time** (`_copy_files`), where the original path and the add argument are both in scope
and each file is already being measured. Originals are never touched; capture is pure reading.

- The `add` argument (the resolved `directory`) is threaded to `_copy_files` so the add-relative rule can be computed:
  `source_dir = track.path.parent.relative_to(directory.parent)`.
- Raw tags are read from the **original** (`track.path`), not the copy, so capture reflects what the source actually
  read — and read once, reusing the open file where practical alongside `tags.measure`.
- Capture writes `File.source_dir` and the `FileTagRaw` rows in the same unit as the `File` insert. It must not touch
  claim assembly or `merge()`: source input is inert to the merge.

A new function in `tags.py` reads the raw tag set — see the mutagen note. `tags.measure` already opens each file; the
raw read can sit beside it (`measure` and `read_raw_tags`, or one combined read) so a file is opened once.

## Could raw tags become the substrate claims are derived from?

Question 6: store raw, then *project* the `file_tags` claims from the raw set instead of reading them separately. It is
attractive — one read, claims provably derived from the captured input — but the plan **declines it for now** and keeps
the existing `read_tags` path beside raw capture. Reasons:

- mediafile's curation is doing real work: format-agnostic field mapping, multi-value handling, the year/date parsing,
  the empty-string-is-absent rule (`_text`). Re-deriving claims from raw mutagen keys means re-implementing that mapping
  for every format — scope this plan should not absorb, and a regression risk against landed behaviour.
- The two readers answer different questions. `read_tags` answers "what does this file claim?" (curated, typed,
  cross-format). Raw capture answers "what frames does this file literally carry?" Keeping them separate is the honest
  split; collapsing them couples claim semantics to capture storage.

It is a good future simplification once the raw layer is proven and a mapping table exists — noted, not built. The plan
leaves the seam clean: both read the same original at copy time.

## mutagen, not mediafile, for the raw read

mediafile deliberately exposes only curated fields — it cannot enumerate the complete native tag set. The full-tag
capture must go **below** mediafile to **mutagen** (which mediafile already wraps, so it is a transitive dependency
today). The plan promotes mutagen to a **direct** dependency (`uv add mutagen`) and confines its use to one new function
in `tags.py` (`read_raw_tags(path) -> list[tuple[str, str]]` or similar), keeping the rest of the codebase on mediafile
per house convention. The convention note in CLAUDE.md ("File tag I/O goes through mediafile") gets a one-line caveat:
*full native-tag capture goes through mutagen, the one place below mediafile.*

mutagen returns format-specific objects (`ID3`, `VComment`, `MP4Tags`); the function normalises them to
`(key, value, ordinal)` triples without renaming keys — frame IDs and atom names stay native. Binary frames (APIC
artwork, etc.) need a policy: the plan's recommendation is to **capture text frames only** in the first cut and skip
binary payloads (artwork is an attachment concern, deferred in the roadmap's "Later"). This is called out as an open
question with that recommendation.

## Portability and the dump

portability.md: the dump serialises **claims and history, never the merged view**. Source input is neither claim nor
merged view — it is source *data*. The recommendation: **source input belongs in the dump.** The dump's purpose is that
the database is a rebuildable index of the dump (losing the merged view is an inconvenience; losing source data is data
loss). Raw tags and the source directory are precisely *source data we chose to preserve so it is not lost* — excluding
them from the dump would reintroduce the loss this whole effort prevents. The dump format is not yet built (roadmap
"Later"), so this plan only **records the requirement**: when `leek dump` is specified, source input is part of it,
alongside claims. No dump code here.

## Surfacing

Display is **out of scope** (question 8). The natural consumer is the merge review queue (roadmap slice 10), which is
where "the `file_tags` source read these tags and claimed this" earns a screen. `leek show --sources` is the other
plausible surface. The plan notes both as where source input *would* surface and builds neither — capture first, display
when a consumer earns it (the same discipline ADR 0033 used for claim-only fields).

## Harness and fixtures

The fixture corpus needs two additions to exercise capture:

1. **Richer raw tags.** Today materialise writes only the mapped fields. To test full-tag capture, at least one fixture
   album must carry tags *beyond* the mapped set — e.g. a `comment`, a `composer`, a `MUSICBRAINZ_*` identifier — so the
   test can assert those survive into `file_tags_raw` while never becoming claims. The corpus schema gains an optional
   per-album (or per-track) `extra_tags` table of native-ish keys, and `materialise_album` writes them. *Sparse* must
   stay sparse (Polder Arcade's *Tape Hiss Archipelago* keeps its absences) — the extra tags go on a fixture chosen for
   it (Aurelia Fenn's clean control is the safe home, or a new fixture if extras would muddy the baseline; lean toward a
   new small fixture so the control stays pristine per the README's standing instruction).
2. **A multi-disc layout.** No fixture today is multi-disc, so the per-file `source_dir` rule (`CD1`/`CD2`) is
   untestable. `materialise_album` writes a flat directory; it needs an optional per-track `disc`/subdirectory so a
   fixture materialises into `CD1/…` and `CD2/…`. A new small multi-disc fixture is the cleanest carrier (the existing
   albums are single-disc by deliberate role and should stay so). The harness change is confined to `materialise.py` and
   `corpus.toml`; `path_names.toml` is untouched (it tests the parser, not capture).

Tests (verification-first, per project-principles):

- **Raw tags**: an album with extra tags materialises, `add`, then assert every native key/value (including the unmapped
  extras and multi-value ordinals) is present in `file_tags_raw`, and that the extras produced **no** `source_values`
  rows. Round-trips FLAC (Vorbis) and MP3 (ID3) since the corpus already exercises both.
- **Source directory**: a multi-disc fixture `add`ed asserts each file's `source_dir` is the add-relative parent
  (`Album/CD1`, `Album/CD2`); a flat album asserts the single-component form; confirm `source_path` is unchanged and
  `_refuse_readds` still refuses on the absolute path.
- **No merge impact**: an existing add test's claim/merge assertions stay green — capture is inert.

## Slice breakdown

Two slices. They are independent (different inputs, different storage shapes, different harness needs), each
implementable and verifiable in one session, each ending runnable — which is the project-principles bar. Sequencing is
free; raw tags is the meatier of the two (mutagen, binary-frame policy), the source directory the more contained.

- **Slice A — capture the source directory.** Add `files.source_dir` (migration), compute the add-relative rule in
  `_copy_files`, thread the add argument through. Multi-disc fixture + materialise `disc` support + tests. Smaller, no
  new dependency. Ends runnable: `add` a multi-disc album and the per-file directories are stored.
- **Slice B — capture raw tags.** Add `file_tags_raw` (migration), promote mutagen to a direct dep, add
  `tags.read_raw_tags`, write the rows at copy time. Extra-tags fixture + materialise support + tests, including the
  "extras are not claims" assertion. Ends runnable: `add` a richly-tagged album and the complete native tag set is
  stored.

The shared **concept** (source input) and its glossary entry land with whichever slice goes first; the second slice
extends it. The ADR that names the concept (below) should land with the first slice so the second has it to cite.

Recommendation on order: **Slice A first** (contained, no dependency, proves the file-level capture seam), then **Slice
B** (the tag-shaped capture, building on the established concept). The reverse also works; A-first is lower risk.

## ADRs to write

Identified, not yet drafted (numbers reserved via `just adr-new` at implementation time; do not hand-number):

1. **"Source input is a third category" (or similar).** The load-bearing one: names *source input* as a category beside
   claim and measurement, states the discriminator (attributable + preserved, but inert to merge), and rules that it
   belongs in the dump. Passes both ADR tests — non-obvious from code (it reshapes the ADR 0007 mental model) and stable
   (the category outlives both slices and anticipates MusicBrainz's raw response). Lands with the first slice.
2. **"Capture raw tags verbatim, below mediafile, in a normalised table."** Records the mutagen-not-mediafile exception,
   the native-keys-verbatim rule, the table-over-JSON choice, and the binary-frame policy. Lands with Slice B. (Possibly
   foldable into ADR 1 if it stays small, but the mediafile exception is a distinct, citable ruling.)

The source-directory rule and the `source_dir`/`source_path` coexistence are arguably re-derivable from the schema + the
ADR-1 concept, so they may not need their own ADR — surface in the slice plan and let ADR 1 carry the principle. If the
re-add interaction proves subtle in implementation, promote it.

## Open questions, each with a recommendation

1. **Binary frames in raw tags?** *Recommendation: text frames only in the first cut; skip binary payloads (artwork).*
   Artwork is an attachment concern, deferred in the roadmap. Revisit when attachments arrive.
2. **One ADR or two?** *Recommendation: two — the concept (ADR 1, with the first slice) and the mutagen/storage ruling
   (ADR 2, with Slice B).* Fold to one only if ADR 2 stays trivially small.
3. **Project claims from raw tags (question 6)?** *Recommendation: no, not now.* Keep `read_tags` beside raw capture;
   revisit as a simplification once the raw layer is proven.
4. **Extra-tags fixture: extend the control or add a new fixture?** *Recommendation: add a new small fixture* so Aurelia
   Fenn's control stays pristine (README standing instruction). Same for the multi-disc layout.
5. **`source_dir` for a flat single-disc album — store the one component, or empty when it equals the add basename?**
   *Recommendation: always store the add-relative parent, even when it is the single add-basename component* (the goal's
   flat-album example shows exactly this), so the column is uniformly populated and the rule has no special case.
6. **Capture the original's mtime/path shape beyond the directory?** *Recommendation: no — `source_path` already holds
   the absolute original and `mtime` is measured on the copy; source input adds only the two inputs named here.* Resist
   scope creep.

______________________________________________________________________

Branch: `raw-source-capture-plan`. This document: `docs/plans/2026-06-15-raw-source-capture.md`.
