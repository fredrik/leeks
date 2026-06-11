# Beets Plugin Inventory & Analysis

**Total: ~80 plugins** (74 single-file + 6 multi-file directories)

______________________________________________________________________

## Plugins Grouped by Area

### Metadata Sources (17 plugins)

| Plugin             | Lines      | Commits (all-time / since 2023) | Notes                          |
| ------------------ | ---------- | ------------------------------- | ------------------------------ |
| **musicbrainz**    | 808        | 71 / 71                         | Core MB search                 |
| **discogs**        | 1030 (dir) | — / 12                          | Discogs autotagger             |
| **beatport**       | 522        | 76 / 20                         | Beatport search                |
| **deezer**         | 287        | 90 / 60                         | Deezer search                  |
| **spotify**        | 816        | 232 / 81                        | Spotify search + playlists     |
| **acousticbrainz** | 304        | 72 / 11                         | AB metadata (service defunct)  |
| **chroma**         | 371        | 94 / 15                         | Acoustic fingerprinting        |
| **lastgenre**      | 709 (dir)  | 317 / 147                       | Genre tagging via Last.fm      |
| **lyrics**         | 1142       | 380 / 90                        | Lyrics fetching                |
| **listenbrainz**   | 273        | 76 / 76                         | Play count import              |
| **lastimport**     | 195        | 58 / 17                         | Last.fm play count             |
| **parentwork**     | 226        | — / 8                           | MB parent work/composer        |
| **mbcollection**   | 233        | 51 / 10                         | MB collection sync             |
| **mbpseudo**       | 350        | — / 17                          | MB pseudo-releases             |
| **absubmit**       | 223        | 44 / 11                         | Submit to AcousticBrainz       |
| **fromfilename**   | 168        | 40 / 14                         | Extract metadata from filename |
| **ftintitle**      | 358        | 105 / 37                        | Move feat. artists to title    |

### Audio Analysis (4 plugins)

| Plugin         | Lines | Commits (all-time / since 2023) | Notes                                 |
| -------------- | ----- | ------------------------------- | ------------------------------------- |
| **replaygain** | 1576  | 275 / 35                        | ReplayGain calculation — very complex |
| **autobpm**    | 88    | — / 12                          | BPM via Librosa                       |
| **bpm**        | 89    | — / 5                           | Manual BPM tap                        |
| **keyfinder**  | 92    | 48 / 7                          | Musical key detection                 |

### Artwork (3 plugins)

| Plugin         | Lines | Commits (all-time / since 2023) | Notes                                                  |
| -------------- | ----- | ------------------------------- | ------------------------------------------------------ |
| **fetchart**   | 1614  | 314 / 72                        | Multi-source art fetching — largest single-file plugin |
| **embedart**   | 290   | 171 / 33                        | Embed art into files                                   |
| **thumbnails** | 289   | 58 / 14                         | Freedesktop thumbnails                                 |

### Playback / Media Server Integration (8 plugins)

| Plugin             | Lines      | Commits (all-time / since 2023) | Notes                                   |
| ------------------ | ---------- | ------------------------------- | --------------------------------------- |
| **bpd**            | 1943 (dir) | 174 / 25                        | Full MPD clone — largest plugin overall |
| **mpdstats**       | 385        | 84 / 8                          | MPD play count gathering                |
| **mpdupdate**      | 129        | — / 4                           | MPD library update                      |
| **embyupdate**     | 215        | — / 9                           | Emby library update                     |
| **kodiupdate**     | 105        | — / 4                           | Kodi library update                     |
| **plexupdate**     | 120        | — / 4                           | Plex library update                     |
| **sonosupdate**    | 47         | — / 2                           | Sonos library update                    |
| **subsonicupdate** | 159        | 40 / 8                          | Subsonic library update                 |

### Import Pipeline (10 plugins)

| Plugin           | Lines | Commits (all-time / since 2023) | Notes                       |
| ---------------- | ----- | ------------------------------- | --------------------------- |
| **filefilter**   | 78    | — / 2                           | Regex file filter           |
| **importadded**  | 156   | — / 5                           | Preserve mtime on import    |
| **importfeeds**  | 152   | 57 / 6                          | Write import paths to M3U   |
| **importsource** | 169   | — / 4                           | Track source path + cleanup |
| **ihate**        | 80    | — / 3                           | Block unwanted imports      |
| **badfiles**     | 218   | 43 / 9                          | Audio integrity check       |
| **duplicates**   | 411   | 90 / 11                         | Duplicate detection         |
| **edit**         | 396   | 89 / 13                         | Edit metadata in $EDITOR    |
| **hook**         | 91    | 45 / 5                          | Run commands on events      |
| **permissions**  | 122   | — / 4                           | Fix file permissions        |

### Tag / Field Manipulation (9 plugins)

| Plugin              | Lines | Commits (all-time / since 2023) | Notes                           |
| ------------------- | ----- | ------------------------------- | ------------------------------- |
| **zero**            | 169   | 61 / 11                         | Clear tag fields                |
| **scrub**           | 151   | 60 / 7                          | Strip extraneous tags           |
| **rewrite**         | 75    | — / 3                           | Rewrite field values            |
| **advancedrewrite** | 176   | — / 10                          | Query-based field rewrite       |
| **replace**         | 127   | — / 2                           | Replace audio file keeping tags |
| **substitute**      | 53    | — / 16                          | Substitution rules for paths    |
| **the**             | 102   | 40 / 8                          | Move articles (The, A)          |
| **titlecase**       | 258   | — / 4                           | NYT-style title casing          |
| **albumtypes**      | 73    | — / 5                           | Format album type field         |

### Playlist (3 plugins)

| Plugin               | Lines | Commits (all-time / since 2023) | Notes                       |
| -------------------- | ----- | ------------------------------- | --------------------------- |
| **smartplaylist**    | 397   | 114 / 32                        | Query-based smart playlists |
| **playlist**         | 206   | — / 15                          | M3U playlist matching       |
| **subsonicplaylist** | 184   | — / 5                           | Subsonic playlist sync      |

### Web / API (4 plugins)

| Plugin     | Lines     | Commits (all-time / since 2023) | Notes                    |
| ---------- | --------- | ------------------------------- | ------------------------ |
| **web**    | 554 (dir) | 154 / 24                        | Web UI for beets         |
| **aura**   | 981       | — / 17                          | AURA standard API server |
| **ipfs**   | 312       | 69 / 9                          | IPFS sharing             |
| **export** | 244       | — / 7                           | JSON/XML/CSV export      |

### Interoperability / Sync (4 plugins)

| Plugin       | Lines     | Commits (all-time / since 2023) | Notes                     |
| ------------ | --------- | ------------------------------- | ------------------------- |
| **metasync** | 386 (dir) | — / 12                          | Sync with Amarok/iTunes   |
| **mbsync**   | 187       | 88 / 13                         | Re-sync from MusicBrainz  |
| **bpsync**   | 187       | — / 11                          | Re-sync from Beatport     |
| **convert**  | 815       | 259 / 48                        | Transcode to external dir |

### Shell / CLI / Query (9 plugins)

| Plugin      | Lines | Commits (all-time / since 2023) | Notes                        |
| ----------- | ----- | ------------------------------- | ---------------------------- |
| **fish**    | 300   | — / 7                           | Fish shell completions       |
| **play**    | 255   | 95 / 10                         | Send query results to player |
| **info**    | 238   | 68 / 5                          | Show file metadata           |
| **random**  | 158   | 45 / 13                         | Random track/album           |
| **limit**   | 95    | — / 4                           | Head/tail for queries        |
| **fuzzy**   | 63    | — / 5                           | Fuzzy query matching         |
| **bareasc** | 95    | — / 7                           | ASCII-normalized queries     |
| **bucket**  | 245   | — / 5                           | %bucket{} path template      |
| **inline**  | 134   | 51 / 7                          | Inline Python in templates   |

### Utility / Internal (6 plugins)

| Plugin          | Lines | Commits (all-time / since 2023) | Notes                      |
| --------------- | ----- | ------------------------------- | -------------------------- |
| **bench**       | 132   | — / 5                           | Performance benchmarks     |
| **loadext**     | 45    | — / 3                           | Load SQLite extensions     |
| **types**       | 49    | — / 3                           | Custom field type defs     |
| **freedesktop** | 38    | — / 2                           | Deprecated → thumbnails    |
| **mbsubmit**    | 98    | — / 7                           | Submit data to MusicBrainz |
| **unimported**  | 66    | — / 3                           | Find orphan files          |

______________________________________________________________________

## Maturity / Complexity / Size Ratings

| Plugin               | Size      | Complexity | Maturity   | Churn (2023+) |
| -------------------- | --------- | ---------- | ---------- | ------------- |
| **bpd**              | XL (1943) | High       | Mature     | Low           |
| **fetchart**         | XL (1614) | High       | Mature     | High          |
| **replaygain**       | XL (1576) | High       | Mature     | Medium        |
| **lyrics**           | L (1142)  | High       | Mature     | High          |
| **discogs**          | L (1030)  | Medium     | Mature     | Low           |
| **aura**             | L (981)   | Medium     | Medium     | Medium        |
| **spotify**          | L (816)   | Medium     | Active     | High          |
| **convert**          | L (815)   | High       | Mature     | Medium        |
| **musicbrainz**      | L (808)   | Medium     | Active     | High          |
| **lastgenre**        | M (709)   | Medium     | Active     | Very High     |
| **web**              | M (554)   | Medium     | Mature     | Medium        |
| **beatport**         | M (522)   | Medium     | Mature     | Medium        |
| **duplicates**       | M (411)   | Medium     | Mature     | Low           |
| **smartplaylist**    | M (397)   | Medium     | Mature     | Medium        |
| **edit**             | M (396)   | Medium     | Mature     | Low           |
| **mpdstats**         | M (385)   | Medium     | Mature     | Low           |
| **metasync**         | M (386)   | Medium     | Mature     | Low           |
| **chroma**           | M (371)   | Medium     | Mature     | Low           |
| **ftintitle**        | M (358)   | Medium     | Active     | Medium        |
| **mbpseudo**         | M (350)   | Medium     | New        | Medium        |
| **ipfs**             | S (312)   | Low        | Stale      | Low           |
| **acousticbrainz**   | S (304)   | Low        | Deprecated | Dormant       |
| **fish**             | S (300)   | Low        | Medium     | Low           |
| **embedart**         | S (290)   | Low        | Mature     | Medium        |
| **thumbnails**       | S (289)   | Low        | Mature     | Low           |
| **deezer**           | S (287)   | Low        | New        | High          |
| **missing**          | S (284)   | Low        | Mature     | Medium        |
| **listenbrainz**     | S (273)   | Low        | New        | High          |
| **titlecase**        | S (258)   | Low        | Medium     | Low           |
| **play**             | S (255)   | Low        | Mature     | Low           |
| **bucket**           | S (245)   | Low        | Mature     | Low           |
| **export**           | S (244)   | Low        | Mature     | Low           |
| **info**             | S (238)   | Low        | Mature     | Low           |
| **mbcollection**     | S (233)   | Low        | Mature     | Low           |
| **parentwork**       | S (226)   | Low        | Mature     | Low           |
| **absubmit**         | S (223)   | Low        | Stale      | Low           |
| **badfiles**         | S (218)   | Low        | Mature     | Low           |
| **embyupdate**       | S (215)   | Low        | Mature     | Low           |
| **playlist**         | S (206)   | Low        | Active     | Medium        |
| **lastimport**       | S (195)   | Low        | Mature     | Medium        |
| **mbsync**           | S (187)   | Low        | Mature     | Low           |
| **bpsync**           | S (187)   | Low        | Medium     | Low           |
| **subsonicplaylist** | S (184)   | Low        | Medium     | Low           |
| **advancedrewrite**  | S (176)   | Low        | New        | Low           |
| **zero**             | S (169)   | Low        | Mature     | Low           |
| **importsource**     | S (169)   | Low        | Medium     | Low           |
| **fromfilename**     | S (168)   | Low        | Mature     | Low           |
| **subsonicupdate**   | S (159)   | Low        | Mature     | Low           |
| **random**           | S (158)   | Low        | Mature     | Low           |
| **importadded**      | S (156)   | Low        | Mature     | Low           |
| **importfeeds**      | S (152)   | Low        | Mature     | Low           |
| **scrub**            | S (151)   | Low        | Mature     | Low           |
| **inline**           | S (134)   | Low        | Mature     | Low           |
| **bench**            | S (132)   | Low        | Internal   | Low           |
| **mpdupdate**        | S (129)   | Low        | Mature     | Low           |
| **replace**          | S (127)   | Low        | Medium     | Dormant       |
| **permissions**      | S (122)   | Low        | Mature     | Low           |
| **plexupdate**       | S (120)   | Low        | Mature     | Low           |
| **kodiupdate**       | S (105)   | Low        | Mature     | Low           |
| **the**              | S (102)   | Low        | Mature     | Low           |
| **mbsubmit**         | XS (98)   | Low        | Medium     | Low           |
| **limit**            | XS (95)   | Low        | Mature     | Low           |
| **bareasc**          | XS (95)   | Low        | Medium     | Low           |
| **keyfinder**        | XS (92)   | Low        | Mature     | Low           |
| **hook**             | XS (91)   | Low        | Mature     | Low           |
| **bpm**              | XS (89)   | Low        | Mature     | Low           |
| **autobpm**          | XS (88)   | Low        | New        | Low           |
| **ihate**            | XS (80)   | Low        | Mature     | Low           |
| **filefilter**       | XS (78)   | Low        | Mature     | Dormant       |
| **rewrite**          | XS (75)   | Low        | Mature     | Dormant       |
| **albumtypes**       | XS (73)   | Low        | Medium     | Low           |
| **unimported**       | XS (66)   | Low        | Medium     | Low           |
| **fuzzy**            | XS (63)   | Low        | Mature     | Low           |
| **substitute**       | XS (53)   | Low        | Medium     | Medium        |
| **types**            | XS (49)   | Low        | Mature     | Low           |
| **sonosupdate**      | XS (47)   | Low        | Low        | Dormant       |
| **loadext**          | XS (45)   | Low        | Low        | Low           |
| **freedesktop**      | XS (38)   | Low        | Deprecated | Dormant       |

### Size scale

| Rating | Lines   |
| ------ | ------- |
| XL     | 1000+   |
| L      | 500–999 |
| M      | 300–499 |
| S      | 100–299 |
| XS     | < 100   |

______________________________________________________________________

## Usage Popularity (from issue/config analysis)

Ranked by how often each plugin appears in user configs extracted from GitHub issues.

| Rank | Plugin             | In Config | Area                          |
| ---- | ------------------ | --------- | ----------------------------- |
| 1    | **fetchart**       | 495       | Artwork                       |
| 2    | **embedart**       | 329       | Artwork                       |
| 3    | **lastgenre**      | 274       | Metadata Sources              |
| 4    | **chroma**         | 267       | Metadata Sources              |
| 5    | **convert**        | 226       | Interop / Sync                |
| 6    | **duplicates**     | 215       | Import Pipeline               |
| 7    | **lyrics**         | 213       | Metadata Sources              |
| 8    | **info**           | 210       | Shell / CLI                   |
| 9    | **discogs**        | 203       | Metadata Sources              |
| 10   | **scrub**          | 196       | Tag Manipulation              |
| 11   | **replaygain**     | 191       | Audio Analysis                |
| 12   | **fromfilename**   | 182       | Metadata Sources              |
| 13   | **web**            | 181       | Web / API                     |
| 14   | **inline**         | 173       | Shell / CLI                   |
| 15   | **missing**        | 166       | Metadata Sources              |
| 16   | **mbsync**         | 151       | Interop / Sync                |
| 17   | **edit**           | 126       | Import Pipeline               |
| 18   | **ftintitle**      | 105       | Metadata Sources              |
| 19   | **zero**           | 90        | Tag Manipulation              |
| 20   | **badfiles**       | 87        | Import Pipeline               |
| 21   | **play**           | 70        | Shell / CLI                   |
| 22   | **smartplaylist**  | 69        | Playlist                      |
| 23   | **acousticbrainz** | 69        | Metadata Sources (deprecated) |
| 24   | **fuzzy**          | 56        | Shell / CLI                   |
| 25   | **random**         | 54        | Shell / CLI                   |
| 26   | **the**            | 49        | Tag Manipulation              |
| 27   | **mbsubmit**       | 45        | Utility                       |
| 28   | **mbcollection**   | 39        | Metadata Sources              |
| 29   | **musicbrainz**    | 36        | Metadata Sources              |
| 30   | **beatport**       | 34        | Metadata Sources              |
| 31   | **spotify**        | 34        | Metadata Sources              |
| 32   | **rewrite**        | 33        | Tag Manipulation              |
| 33   | **mpdupdate**      | 30        | Media Servers                 |
| 34   | **importadded**    | 30        | Import Pipeline               |
| 35   | **types**          | 29        | Utility                       |
| 36   | **thumbnails**     | 29        | Artwork                       |
| 37   | **bpd**            | 27        | Media Servers                 |
| 38   | **mpdstats**       | 24        | Media Servers                 |
| 39   | **lastimport**     | 24        | Metadata Sources              |
| 40   | **permissions**    | 23        | Import Pipeline               |
| 41   | **bucket**         | 16        | Shell / CLI                   |
| 42   | **absubmit**       | 16        | Metadata Sources              |
| 43   | **unimported**     | 14        | Utility                       |
| 44   | **importfeeds**    | 13        | Import Pipeline               |
| 45   | **deezer**         | 13        | Metadata Sources              |
| 46   | **parentwork**     | 12        | Metadata Sources              |
| 47   | **bpm**            | 11        | Audio Analysis                |
| 48   | **plexupdate**     | 11        | Media Servers                 |
| 49   | **hook**           | 11        | Import Pipeline               |
| 50   | **export**         | 11        | Web / API                     |
| 51   | **playlist**       | 11        | Playlist                      |
| 52   | **autobpm**        | 10        | Audio Analysis                |
| 53   | **albumtypes**     | 9         | Tag Manipulation              |
| 54   | **metasync**       | 8         | Interop / Sync                |
| 55   | **keyfinder**      | 6         | Audio Analysis                |
| 56   | **ihate**          | 6         | Import Pipeline               |
| 57   | **fish**           | 3         | Shell / CLI                   |
| 58   | **bareasc**        | 3         | Shell / CLI                   |
| 59   | **subsonicupdate** | 2         | Media Servers                 |
| 60   | **mbpseudo**       | 2         | Metadata Sources              |
| 61   | **freedesktop**    | 1         | Utility (deprecated)          |
| 62   | **filefilter**     | 1         | Import Pipeline               |
| 63   | **ipfs**           | 1         | Web / API                     |
| 64   | **embyupdate**     | 1         | Media Servers                 |
| 65   | **loadext**        | 1         | Utility                       |
| 66   | **bpsync**         | 1         | Interop / Sync                |
| 67   | **substitute**     | 1         | Tag Manipulation              |
| 68   | **listenbrainz**   | 1         | Metadata Sources              |
| 69   | **bench**          | 1         | Utility                       |
| 70   | **titlecase**      | 1         | Tag Manipulation              |

### Usage tiers

| Tier                 | Config count | Plugins                                                                                                                                                                                    |
| -------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Essential** (100+) | 105–495      | fetchart, embedart, lastgenre, chroma, convert, duplicates, lyrics, info, discogs, scrub, replaygain, fromfilename, web, inline, missing, mbsync, edit, ftintitle                          |
| **Popular** (25–99)  | 25–90        | zero, badfiles, play, smartplaylist, acousticbrainz, fuzzy, random, the, mbsubmit, mbcollection, musicbrainz, beatport, spotify, rewrite, mpdupdate, importadded, types, thumbnails, bpd   |
| **Niche** (5–24)     | 5–24         | mpdstats, lastimport, permissions, bucket, absubmit, unimported, importfeeds, deezer, parentwork, bpm, plexupdate, hook, export, playlist, autobpm, albumtypes, metasync, keyfinder, ihate |
| **Rare** (1–4)       | 1–4          | fish, bareasc, subsonicupdate, mbpseudo, freedesktop, filefilter, ipfs, embyupdate, loadext, bpsync, substitute, listenbrainz, bench, titlecase                                            |

______________________________________________________________________

## Key Observations

### Hottest plugins (most active since 2023)

lastgenre (147 commits), lyrics (90), spotify (81), listenbrainz (76), fetchart (72), musicbrainz (71), deezer (60). All
metadata source plugins — reflecting ongoing upstream API churn.

### Largest / most complex

- **bpd** (1943 lines) — a full MPD server implementation
- **fetchart** (1614 lines) — multi-source art fetching with fallback chains
- **replaygain** (1576 lines) — multiple backends (ffmpeg, gstreamer, bs1770gain)
- **lyrics** (1142 lines) — multiple scraper backends
- **convert** (815 lines) — transcoding pipeline with queue management

### Likely deprecated / stale

- **acousticbrainz** — service shut down in 2022
- **freedesktop** — just redirects to thumbnails plugin
- **ipfs** — niche, very low activity

### Usage vs development investment

- **Artwork plugins dominate usage** — fetchart (495) and embedart (329) are #1 and #2 by a wide margin, yet they're
  relatively mature and stable.
- **High churn, low usage** — listenbrainz has 76 commits since 2023 but only 1 config mention. deezer has 60 commits
  but only 13 mentions. These represent heavy investment in under-adopted plugins.
- **High usage, low churn** — scrub (196 configs, 7 recent commits), inline (173 configs, 7 recent commits),
  fromfilename (182 configs, 14 recent commits). These are reliable workhorses that need little maintenance.
- **acousticbrainz still has 69 config mentions** despite the service being defunct since 2022 — suggesting many users
  have stale configs.

### Structural patterns

- **Media server update plugins** (emby, kodi, plex, sonos, subsonic) are all small (47–215 lines) and structurally
  near-identical. Could be refactored into a single generic "notify server" plugin with per-server config.
- **Metadata source plugins** form the core of the project and see by far the most churn — driven by external API
  changes.
- **Import pipeline plugins** are mostly small, stable, and self-contained — a sign of good plugin architecture.
- **Clear split between "fetch data" and "transform data" plugins**, with the latter being much more stable over time.
- **Multi-file plugins** (bpd, discogs, lastgenre, web, metasync) tend to be the most complex, justifying their
  directory structure.
