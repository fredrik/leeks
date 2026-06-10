# leeks

leeks is a music library organiser and spiritual successor to beets, built around albums rather than files. It keeps a
normalised relational schema, layers multiple metadata sources, and records a full event history of every edit. Like git
for your music library's metadata.

## Status

leeks is in early development and is not ready for general consumption. This README is currently more of a manifesto
than manual, and that's deliberate.

## How to get started

```
uv tool install leeks
leek init
leek import ~/Downloads
```

## Why another music organiser?

leeks comes out of years of using beets on a ~25k track library.

beets is excellent, and most of what's good about leeks is borrowed from it, but beets and I disagree on something
fundamental: how to model the collection.

beets is built bottom-up from the file, which represents a track. The album is whatever emerges when you group files
with matching tags. The same goes for artists, who are just names with no additional metadata. There is no explicit
connection between two albums by the same artist. Edit the album's name and you've edited every track on it: eighteen
rows, eighteen file tags written, maybe done.

leeks is built top-down from the album. The album is a first-class entity with its own identity, independent of any file
on disk. Tracks belong to it. Files realise tracks. Edit the album's name and you've edited the album: one row, one
change, done.

None of this is novel. It's normalisation, applied to a domain that somehow ended up without it.

## Why layered sources?

The album-first model is what invites the layered architecture.

If the file is primary, you don't need layers. Each file has its tags and that's the truth. MusicBrainz lookups are
corrections written back to the file. Whichever source ran last wins, and that's fine because there's only one slot to
write to.

If the album is primary, the question "what is this album called, who's it by, when did it come out" has multiple
legitimate answers depending on who you ask. The 2001 Modular CD says one thing. MusicBrainz says another. Discogs
disagrees with both. Your file tags from a 2008 rip say a fourth. Your own correction says a fifth.

They are not all trying to answer the same question. They're all true about different things: the pressing, the
canonical work, the specific listing on a specific site, what someone typed into iTunes seventeen years ago, what you
decided last Tuesday.

A file-centric tool has to pick a winner. An album-centric tool gets to keep them all and merge them on read. That's
what leeks does.

## Who is leeks for?

leeks is built for people whose music comes from places where provenance is part of the metadata: private archives,
careful rippers, collector communities with well-curated torrents of metadata. They are sources where the upload notes
tell you exactly which pressing this is, and that distinction matters because which version you heard is part of what
the album is to you.

Streaming services have moved the world the other way. On Spotify there is one *Since I Left You* and it's almost always
the maximal version: remastered, expanded, with bonus tracks that weren't on the album you fell in love with. The
original pressing, the one that actually came out in 2001, with the running order the artists signed off on, is often
not available at all.

leeks is for people who notice that, and mind. It's a tool for collections where the release isn't an implementation
detail. leeks will help you if you have a directory called

```
The Avalanches - Since I Left You (2001) [FLAC] {Scandinavia - XLCD 138}
```

and you want every part of that name to remain meaningful (the original year, the format, the region, the catalogue
number) instead of getting silently flattened or replaced the next time something runs a metadata sync.

## Departures from beets

1. **The album is the model, not the file.** Tracks, releases (specific pressings), and files hang off the album as
   related entities. Artists too: a first-class row with its own identity, not a string that happens to appear in a tag.

1. **Import everything, gate nothing.** Every file enters the library unconditionally. The files that most need
   management are the ones with the worst metadata. Gating them out at import defeats the purpose. Re-fetching from
   matched sources later can only improve what's there; it never has to recover from a failed import.

1. **Sources are layers, not overwrites.** File tags, MusicBrainz, Discogs, tracker upload metadata, your own edits: all
   stored in separate layers, all preserved. The library view is a merge according to configurable priority rules. A
   wrong match is a low-confidence layer you can ignore or delete; nothing irreversible happened.

1. **Every edit is versioned.** All changes (source fetches, user edits, automated updates) are kept with full event
   history. The data model is append-mostly: nothing overwrites, everything accumulates. You can see what MusicBrainz
   said about an album in 2024 versus 2026, when you corrected a track title, what the tracker upload originally
   claimed.

1. **Background fetch, foreground review.** Source fetching runs in the background. Changes land in a pending queue.
   Review is a separate step: human, agent, or automated rule.

1. **Non-destructive by default.** Tag writing, renaming, and moving files are explicit and separate actions, never a
   side effect of import.
