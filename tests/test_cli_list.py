"""The list command at the CLI surface: the shelf, and notes when it is bare."""

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
    # Long enough that the table rendering would wrap it at width 80.
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
    artist, year, title = lines[0].split("\t")
    assert artist.startswith("The Extraordinarily")
    assert year == "2021"
    assert title.endswith("(Deluxe)")


def test_forced_colour_does_not_wrap_a_pipe(shelve, monkeypatch):
    # FORCE_COLOR makes Rich call a pipe a terminal; the pipe is still a
    # pipe (ADR 0011), so the long album stays one plain record, not a
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


def test_list_appears_in_help():
    result = CliRunner().invoke(leek, ["help"])
    assert "list" in result.output


def test_list_tracks_walks_the_tree(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list", "--tracks"])
    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    # One tab record per track: artist, album, number, title.
    assert len(lines) == 5
    artist, album, number, title = lines[0].split("\t")
    assert artist == "Tin Hatch Choir"
    assert album == "Cartography for Sleepwalkers"
    assert number == "1"
    assert title == "Inventory of Small Storms"


def test_list_tracks_narrows_with_terms(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list", "--tracks", "storms"])
    assert result.exit_code == 0
    assert "Inventory of Small Storms" in result.stdout
    assert "Glass Harbour" not in result.stdout


def test_piped_tracks_are_one_line_each(corpus, materialise):
    # The long-named album would wrap a width-80 table; piped, each track
    # stays one greppable record (the slice-2 lesson, now for tracks).
    library.add(materialise(by_title(corpus, "I Wrote My Heart in Beacon Code")))
    result = CliRunner().invoke(leek, ["list", "--tracks"])
    lines = result.stdout.splitlines()
    assert len(lines) == 3
    assert all(len(line.split("\t")) == 4 for line in lines)


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
    result = CliRunner().invoke(leek, ["list", "--tracks", "--artists"])
    assert result.exit_code == 0
    # Artists won: bare name lines, not tab-separated track records.
    assert "Tin Hatch Choir" in result.stdout
    assert "\t" not in result.stdout


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
    lines = result.stdout.splitlines()
    title, artist = lines[0].split("\t")
    assert title == "Cartography for Sleepwalkers"
    assert artist == "Tin Hatch Choir"


def test_fields_trims_whitespace(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list", "--fields", " title , artist "])
    assert result.exit_code == 0
    title, artist = result.stdout.splitlines()[0].split("\t")
    assert title == "Cartography for Sleepwalkers"
    assert artist == "Tin Hatch Choir"


def test_fields_composes_with_tracks(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    result = CliRunner().invoke(leek, ["list", "--tracks", "--fields", "number,title"])
    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert all(len(line.split("\t")) == 2 for line in lines)
    number, title = lines[0].split("\t")
    assert number == "1"
    assert title == "Inventory of Small Storms"


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
    cells = result.stdout.splitlines()[0].split("\t")
    assert len(cells) == 2
    assert cells[0] == cells[1]
