"""The list command at the CLI surface: the shelf, and notes when it is bare."""

import json

from click.testing import CliRunner

from leeks import library
from leeks.cli import leek
from test_harness import by_title


def test_list_prints_the_shelf_in_order(corpus, materialise):
    library.add(materialise(by_title(corpus, "Paper Lung Atlas")))
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list"])
    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert "Tin Hatch Choir" in lines[0]
    assert "2019" in lines[0]
    assert "Cartography for Sleepwalkers" in lines[0]
    assert "Paper Lung Atlas" in lines[1]


def test_list_narrows_with_terms(corpus, materialise):
    library.add(materialise(by_title(corpus, "Paper Lung Atlas")))
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list", "sleepwalkers"])
    assert result.exit_code == 0
    assert "Cartography for Sleepwalkers" in result.stdout
    assert "Paper Lung Atlas" not in result.stdout


def test_a_qualified_term_narrows_to_one_field(corpus, materialise):
    library.add(materialise(by_title(corpus, "Paper Lung Atlas")))  # 2017
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))  # 2019
    result = CliRunner().invoke(leek, ["list", "year:2017"])
    assert result.exit_code == 0
    assert "Paper Lung Atlas" in result.stdout
    assert "Cartography for Sleepwalkers" not in result.stdout


def test_an_unknown_field_is_a_loud_usage_error(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["list", "bogus:x"])
    assert result.exit_code != 0
    assert result.stdout == ""
    assert "bogus" in result.stderr
    assert "choose from" in result.stderr


def test_an_empty_library_points_at_add():
    result = CliRunner().invoke(leek, ["list"])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "leek add" in result.stderr


def test_no_match_is_a_note_not_an_error(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["list", "polka"])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "nothing" in result.stderr


def test_fallbacks_render_but_are_visibly_not_data(shelve):
    shelve("Mystery Tape")
    result = CliRunner().invoke(leek, ["list"])
    assert "Unknown Artist" in result.stdout


def test_piped_albums_are_one_line_each(shelve):
    # A pipe gets bare plain lines, never the wrapping table (ADR 0019), so a
    # very long album stays exactly one line, its fields space-joined.
    shelve(
        "An Album Title That Goes On Considerably Longer Than Anyone Would "
        "Reasonably Expect (Deluxe)",
        artist="The Extraordinarily Long-Winded Orchestral Collective of "
        "Greater Scandinavia",
        year=2021,
    )
    result = CliRunner().invoke(leek, ["list"])
    lines = result.stdout.splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("The Extraordinarily")
    assert "2021" in lines[0]
    assert lines[0].endswith("(Deluxe)")


def test_forced_colour_does_not_wrap_a_pipe(shelve, monkeypatch):
    # FORCE_COLOR makes Rich call a pipe a terminal; the pipe is still a
    # pipe (ADR 0019), so the long album stays one bare line, not a
    # wrapped, ANSI-styled table.
    monkeypatch.setenv("FORCE_COLOR", "1")
    shelve(
        "An Album Title That Goes On Considerably Longer Than Anyone Would "
        "Reasonably Expect (Deluxe)",
        artist="The Extraordinarily Long-Winded Orchestral Collective of "
        "Greater Scandinavia",
        year=2021,
    )
    result = CliRunner().invoke(leek, ["list"])
    lines = result.stdout.splitlines()
    assert len(lines) == 1
    assert "\x1b[" not in result.stdout  # no ANSI escapes leaked into the pipe


def test_list_can_select_id_for_every_subject(corpus, materialise):
    # id is selectable for tracks and artists, not only albums (ADR 0020):
    # the handle a user needs for show id:N, no longer a confusing error.
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    for subject in ("--albums", "--tracks", "--artists"):
        result = CliRunner().invoke(leek, ["list", subject, "--fields", "id"])
        assert result.exit_code == 0, result.output
        # Every line is the bare integer id of one row.
        assert all(line.isdigit() for line in result.stdout.splitlines())


def test_list_summarises_the_count_on_stderr(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["list"])
    assert result.exit_code == 0
    assert "listing 2 albums" in result.stderr
    assert "listing" not in result.stdout  # the count rides stderr, not the list
    one = CliRunner().invoke(leek, ["list", "salt"])
    assert "listing 1 album" in one.stderr  # singular for a count of one


def test_singular_subject_synonyms_are_accepted(corpus, materialise):
    # --track is --tracks; the plural and singular are the same listing.
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    plural = CliRunner().invoke(leek, ["list", "--tracks"])
    singular = CliRunner().invoke(leek, ["list", "--track"])
    assert singular.exit_code == 0
    assert singular.stdout == plural.stdout


def test_list_appears_in_help():
    result = CliRunner().invoke(leek, ["help"])
    assert "list" in result.output


def test_list_tracks_walks_the_tree(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list", "--tracks"])
    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    # One bare line per track: artist, album, number, title, space-joined.
    assert len(lines) == 5
    assert lines[0] == (
        "Tin Hatch Choir Cartography for Sleepwalkers 1 Inventory of Small Storms"
    )


def test_list_tracks_narrows_with_terms(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list", "--tracks", "storms"])
    assert result.exit_code == 0
    assert "Inventory of Small Storms" in result.stdout
    assert "Glass Harbour" not in result.stdout


def test_piped_tracks_are_one_line_each(corpus, materialise):
    # The long-named album would wrap a width-80 table; piped, each track is
    # one bare line instead (ADR 0019), the album name intact on every one.
    library.add(materialise(by_title(corpus, "I Wrote My Heart in Beacon Code")))
    result = CliRunner().invoke(leek, ["list", "--tracks"])
    lines = result.stdout.splitlines()
    assert len(lines) == 3
    assert all("I Wrote My Heart in Beacon Code" in line for line in lines)


def test_forced_colour_does_not_wrap_piped_tracks(corpus, materialise, monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "1")
    library.add(materialise(by_title(corpus, "I Wrote My Heart in Beacon Code")))
    result = CliRunner().invoke(leek, ["list", "--tracks"])
    lines = result.stdout.splitlines()
    assert len(lines) == 3
    assert "\x1b[" not in result.stdout  # no ANSI escapes leaked into the pipe


def test_list_artists_lists_names(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["list", "--artists"])
    assert result.exit_code == 0
    names = result.stdout.splitlines()
    # Salt Meridian brings its album artist and the raw feat. credit row.
    assert "Tin Hatch Choir" in names
    assert "Tin Hatch Choir feat. Vesna Holloway" in names


def test_subject_options_are_mutually_exclusive(corpus, materialise):
    # Shared flag_value: the last subject on the line wins (an explicit
    # error is the deferred mutual-exclusion question, ADR 0013).
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    won = CliRunner().invoke(leek, ["list", "--tracks", "--artists"])
    artists = CliRunner().invoke(leek, ["list", "--artists"])
    assert won.exit_code == 0
    # Artists won, not tracks: identical to a plain --artists listing.
    assert won.stdout == artists.stdout
    assert "Tin Hatch Choir" in won.stdout


def test_empty_library_notes_for_tracks_and_artists():
    tracks = CliRunner().invoke(leek, ["list", "--tracks"])
    assert tracks.exit_code == 0
    assert tracks.stdout == ""
    assert "leek add" in tracks.stderr
    artists = CliRunner().invoke(leek, ["list", "--artists"])
    assert artists.exit_code == 0
    assert artists.stdout == ""
    assert "no artists yet" in artists.stderr


def test_no_match_notes_for_tracks_and_artists(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    tracks = CliRunner().invoke(leek, ["list", "--tracks", "zzz"])
    assert tracks.exit_code == 0
    assert tracks.stdout == ""
    assert "no tracks match that" in tracks.stderr
    artists = CliRunner().invoke(leek, ["list", "--artists", "zzz"])
    assert artists.exit_code == 0
    assert artists.stdout == ""
    assert "no artists match that" in artists.stderr


def test_list_tracks_shows_an_overriding_credit(corpus, materialise):
    # The effective artist (ADR 0013, option A): Lowland Frequencies' own
    # feat. credit reaches the track view, consistent with --artists.
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["list", "--tracks"])
    assert "Tin Hatch Choir feat. Vesna Holloway" in result.stdout


def test_albums_option_matches_the_default(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    explicit = CliRunner().invoke(leek, ["list", "--albums"])
    default = CliRunner().invoke(leek, ["list"])
    assert explicit.exit_code == 0
    assert explicit.stdout == default.stdout
    assert "Salt Meridian" in explicit.stdout


def test_list_options_appear_in_help():
    result = CliRunner().invoke(leek, ["list", "--help"])
    assert "--albums" in result.output
    assert "--tracks" in result.output
    assert "--artists" in result.output


def test_fields_appears_in_help():
    result = CliRunner().invoke(leek, ["list", "--help"])
    assert "--fields" in result.output


def test_fields_selects_a_subset_in_order(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    # title then artist — field order is column order, and these replace
    # the curated columns (no year, no extra).
    result = CliRunner().invoke(leek, ["list", "--fields", "title,artist"])
    assert result.exit_code == 0
    # Column order is field order — title leads — and no year column.
    assert (
        result.stdout.splitlines()[0] == "Cartography for Sleepwalkers Tin Hatch Choir"
    )


def test_fields_trims_whitespace(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list", "--fields", " title , artist "])
    assert result.exit_code == 0
    assert (
        result.stdout.splitlines()[0] == "Cartography for Sleepwalkers Tin Hatch Choir"
    )


def test_fields_composes_with_tracks(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list", "--tracks", "--fields", "number,title"])
    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    # Only number,title, in that order: every line opens with its number.
    assert lines[0] == "1 Inventory of Small Storms"
    assert all(line.split(" ", 1)[0].isdigit() for line in lines)


def test_unknown_field_is_a_loud_error(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["list", "--fields", "nonsense"])
    assert result.exit_code != 0
    # The error names the offender and lists the valid fields, never a silent skip.
    assert "nonsense" in result.output
    assert "artist" in result.output
    assert "title" in result.output


def test_fields_namespace_is_per_subject(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    # 'year' is a valid album field but not an artist field.
    albums = CliRunner().invoke(leek, ["list", "--fields", "year"])
    assert albums.exit_code == 0
    artists = CliRunner().invoke(leek, ["list", "--artists", "--fields", "year"])
    assert artists.exit_code != 0
    assert "year" in artists.output
    assert "name" in artists.output


def test_fields_duplicates_are_kept(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["list", "--fields", "title,title"])
    assert result.exit_code == 0
    # A duplicate field is kept, not deduped: the title prints twice.
    assert result.stdout.splitlines()[0] == "Salt Meridian Salt Meridian"


def test_genres_is_opt_in_not_a_default_column(corpus, materialise):
    library.add(materialise(by_title(corpus, "Genrezvous Telemetry")))
    bare = CliRunner().invoke(leek, ["list"])
    assert bare.exit_code == 0
    # The shelf's identity stays artist/year/title; genres are opt-in (ADR 0022).
    assert "Ambient" not in bare.stdout


def test_genres_field_joins_with_commas_for_the_eye(corpus, materialise):
    library.add(materialise(by_title(corpus, "Genrezvous Telemetry")))
    result = CliRunner().invoke(leek, ["list", "--fields", "title,genres"])
    assert result.exit_code == 0
    assert "Genrezvous Telemetry Ambient, Dub Techno, Field Recording" in result.stdout


def test_genres_json_is_a_real_array(corpus, materialise):
    library.add(materialise(by_title(corpus, "Genrezvous Telemetry")))
    result = CliRunner().invoke(
        leek, ["list", "--fields", "title,genres", "--format", "json"]
    )
    assert result.exit_code == 0
    row = json.loads(result.stdout)[0]
    # JSON keeps the set structured, not stringified (ADR 0022).
    assert row["genres"] == ["Ambient", "Dub Techno", "Field Recording"]


def test_genres_csv_joins_with_semicolons(corpus, materialise):
    import csv as csvmod
    import io

    library.add(materialise(by_title(corpus, "Genrezvous Telemetry")))
    result = CliRunner().invoke(
        leek, ["list", "--fields", "title,genres", "--format", "csv"]
    )
    assert result.exit_code == 0
    rows = list(csvmod.reader(io.StringIO(result.stdout)))
    # A set in one flat cell, joined by "; " so the comma stays CSV's alone.
    assert rows[1] == ["Genrezvous Telemetry", "Ambient; Dub Techno; Field Recording"]


def test_genres_absent_album_is_empty_not_a_fallback(corpus, materialise):
    library.add(materialise(by_title(corpus, "Tape Hiss Archipelago")))
    result = CliRunner().invoke(
        leek, ["list", "--fields", "title,genres", "--format", "json"]
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)[0]["genres"] == []


def test_format_json_is_valid_and_typed(shelve):
    shelve("Salt Meridian", artist="Tin Hatch Choir", year=2021)
    result = CliRunner().invoke(leek, ["list", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    row = payload[0]
    assert row == {"artist": "Tin Hatch Choir", "year": 2021, "title": "Salt Meridian"}
    # The year is a real JSON number, not a stringified one (ADR 0014).
    assert row["year"] == 2021
    assert isinstance(row["year"], int)


def test_format_json_renders_absence_as_null(shelve):
    # The honest-null contrast with the pipe's "Unknown Artist" fallback: a
    # genuine absence is null in JSON, not the display bucket (ADR 0014).
    shelve("Mystery Tape")
    result = CliRunner().invoke(leek, ["list", "--format", "json"])
    assert result.exit_code == 0
    row = json.loads(result.stdout)[0]
    assert row["artist"] is None
    assert "Unknown Artist" not in result.stdout
    assert row["year"] is None


def test_format_json_composes_with_fields_and_tracks(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(
        leek, ["list", "--tracks", "--fields", "artist,number", "--format", "json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    # Exactly the selected keys, in order, with the number typed.
    assert all(set(row) == {"artist", "number"} for row in payload)
    assert isinstance(payload[0]["number"], int)


def test_format_json_empty_library_is_an_empty_array():
    result = CliRunner().invoke(leek, ["list", "--format", "json"])
    assert result.exit_code == 0
    # A machine consumer always parses valid JSON, even on an empty shelf.
    assert json.loads(result.stdout) == []


def test_format_human_matches_the_default(shelve):
    # --format human names the default explicitly (ADR 0019): the readable
    # shape is what you get with no --format, so naming it changes nothing.
    shelve("Salt Meridian", artist="Tin Hatch Choir", year=2021)
    explicit = CliRunner().invoke(leek, ["list", "--format", "human"])
    default = CliRunner().invoke(leek, ["list"])
    assert explicit.exit_code == 0
    assert explicit.stdout == default.stdout


def test_format_csv_has_a_header_and_rows(shelve):
    import csv as csvmod
    import io

    shelve("Salt Meridian", artist="Tin Hatch Choir", year=2021)
    result = CliRunner().invoke(leek, ["list", "--format", "csv"])
    assert result.exit_code == 0
    rows = list(csvmod.reader(io.StringIO(result.stdout)))
    assert rows[0] == ["artist", "year", "title"]  # the spreadsheet header
    assert rows[1] == ["Tin Hatch Choir", "2021", "Salt Meridian"]


def test_format_csv_quotes_embedded_commas(shelve):
    import csv as csvmod
    import io

    shelve("Comma, Comma, Down", artist="Tin Hatch Choir", year=2021)
    result = CliRunner().invoke(leek, ["list", "--format", "csv"])
    # The csv module quotes the comma'd title; it parses back intact, unsplit.
    title = list(csvmod.reader(io.StringIO(result.stdout)))[1][2]
    assert title == "Comma, Comma, Down"


def test_format_csv_leaves_absence_blank_not_the_bucket(shelve):
    import csv as csvmod
    import io

    shelve("Mystery Tape")  # no artist, no year
    result = CliRunner().invoke(leek, ["list", "--format", "csv"])
    row = list(csvmod.reader(io.StringIO(result.stdout)))[1]
    assert row[0] == ""  # absent artist is blank, not "Unknown Artist" (ADR 0019)
    assert "Unknown Artist" not in result.stdout


def test_format_tsv_omits_the_header_for_cut(shelve):
    shelve("Salt Meridian", artist="Tin Hatch Choir", year=2021)
    result = CliRunner().invoke(leek, ["list", "--format", "tsv"])
    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    # No header: the first line is data, so cut -f reads pure values.
    assert lines[0].split("\t") == ["Tin Hatch Choir", "2021", "Salt Meridian"]
    assert "artist\t" not in result.stdout


def test_format_appears_in_help():
    result = CliRunner().invoke(leek, ["list", "--help"])
    assert "--format" in result.output


def test_invalid_format_is_rejected(shelve):
    shelve("Salt Meridian")
    result = CliRunner().invoke(leek, ["list", "--format", "xml"])
    assert result.exit_code != 0


def test_fields_empty_name_is_a_clear_error(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    result = CliRunner().invoke(leek, ["list", "--fields", "artist,"])
    assert result.exit_code != 0
    # A trailing comma blames an empty name, not a cryptic '' is not a field.
    assert "empty field name" in result.output


def test_format_json_is_plain_under_forced_colour(shelve):
    # JSON is for machines: even when colour is forced (Rich would otherwise
    # style a terminal), the structured shape stays pure parseable JSON.
    shelve("Salt Meridian", artist="Tin Hatch Choir", year=2021)
    result = CliRunner(env={"FORCE_COLOR": "1"}).invoke(
        leek, ["list", "--format", "json"]
    )
    assert result.exit_code == 0
    assert "\x1b[" not in result.stdout  # no ANSI escapes leaked into the JSON
    assert json.loads(result.stdout)[0]["year"] == 2021


def test_shelf_table_dresses_fields_in_the_vocabulary():
    # The styled TTY path is unreachable from CliRunner (its stdout is never a
    # tty), so render the table straight to a truecolor console and read the
    # escapes: the artist is mauve (ADR 0024), the year peach.
    from rich.console import Console

    from leeks.cli import _shelf_table
    from leeks.library import Listed

    rows = [Listed(id=1, artist="Tin Hatch Choir", year=2019, title="Salt Meridian")]
    console = Console(width=80, force_terminal=True, color_system="truecolor")
    with console.capture() as capture:
        console.print(_shelf_table(rows))
    out = capture.get()
    assert "38;2;203;166;247" in out  # mauve, the artist's hue (#cba6f7)
    assert "38;2;250;179;135" in out  # peach, the year's hue (#fab387)


def test_unknown_artist_is_not_mauve_but_dim_italic():
    # Absence is not a field (ADR 0024): the Unknown bucket keeps its dim italic
    # (ADR 0010), so the mauve artist hue never lands on a fallback.
    from rich.console import Console

    from leeks.cli import _shelf_table
    from leeks.library import Listed

    rows = [Listed(id=1, artist=None, year=None, title="Mystery Tape")]
    console = Console(width=80, force_terminal=True, color_system="truecolor")
    with console.capture() as capture:
        console.print(_shelf_table(rows))
    out = capture.get()
    assert "Unknown Artist" in out
    assert "38;2;203;166;247" not in out  # no mauve on the fallback


def test_fields_table_keeps_each_field_in_the_vocabulary():
    # --fields is not a plain table: a selected field keeps its hue (ADR 0024),
    # the same it wears in the default view — artist mauve, title bold text.
    from rich.console import Console

    from leeks.cli import _plain_table
    from leeks.library import Listed

    rows = [Listed(id=1, artist="Tin Hatch Choir", year=2019, title="Salt Meridian")]
    console = Console(width=80, force_terminal=True, color_system="truecolor")
    with console.capture() as capture:
        console.print(_plain_table(rows, ("artist", "title")))
    out = capture.get()
    assert "38;2;203;166;247" in out  # artist still mauve under --fields
    assert "1;38;2;205;214;244" in out  # title still bold text


def test_fields_table_unknown_artist_stays_dim_not_mauve():
    # The Unknown bucket keeps its own look under --fields too (ADR 0024/0010):
    # the artist hue lands on real artists, never on the fallback.
    from rich.console import Console

    from leeks.cli import _plain_table
    from leeks.library import Listed

    rows = [Listed(id=1, artist=None, year=None, title="Mystery Tape")]
    console = Console(width=80, force_terminal=True, color_system="truecolor")
    with console.capture() as capture:
        console.print(_plain_table(rows, ("artist", "title")))
    out = capture.get()
    assert "Unknown Artist" in out
    assert "38;2;203;166;247" not in out  # no mauve on the fallback


def test_plain_table_renders_selected_columns():
    # The --fields TTY table: a direct render, because CliRunner's stdout is
    # never a tty, so the table branch is unreachable from the CLI surface.
    from rich.console import Console

    from leeks.cli import _plain_table
    from leeks.library import Listed

    rows = [Listed(id=1, artist=None, year=None, title="Mystery Tape")]
    table = _plain_table(rows, ("artist", "year", "title"))
    assert len(table.columns) == 3
    console = Console(width=80)
    with console.capture() as capture:
        console.print(table)
    out = capture.get()
    # Plain side of the asymmetry: null artist is the Unknown bucket, a null
    # year is empty, and a raw None never leaks (ADR 0010/0014).
    assert "Unknown Artist" in out
    assert "Mystery Tape" in out
    assert "None" not in out
