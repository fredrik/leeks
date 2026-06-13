"""The leek command-line interface."""

import importlib.metadata
import json
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import rich_click as click
from rich.console import Console
from rich.live import Live
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from leeks import theme

if TYPE_CHECKING:
    from leeks.library import (
        Added,
        Claim,
        Listed,
        ListedArtist,
        ListedTrack,
        ShownAlbum,
        ShownFile,
        ShownTrack,
    )

theme.apply()

SPARKLE_SECONDS = 1.2
SPARKLE_FPS = 24


def _print_about() -> None:
    """The short and sweet greeting; the full story lives in `leek help`."""
    console = Console()
    console.print()
    console.print(
        Text.assemble(
            theme.rainbow("leek"),
            (", a music library organiser", f"bold {theme.TEXT}"),
        )
    )
    console.print(Text("the spiritual successor to beets", style=theme.SUBTEXT0))
    console.print()
    console.print(
        Text.assemble(
            ("run ", theme.SUBTEXT0),
            ("leek help", f"bold {theme.BLUE}"),
            (" to see what it can do", theme.SUBTEXT0),
        )
    )


# invoke_without_command: a bare `leek` greets with the about card, not help.
@click.group(invoke_without_command=True)
@click.pass_context
def leek(ctx: click.Context) -> None:
    """A music library organiser, and the spiritual successor to beets."""
    if ctx.invoked_subcommand is None:
        _print_about()


def _version_line(version: str, offset: int) -> Text:
    return Text.assemble(
        theme.rainbow("leek", offset), (f", version {version}", theme.TEXT)
    )


@leek.command()
def version() -> None:
    """Show the leek version."""
    installed = importlib.metadata.version("leeks")
    console = Console()
    # The sparkle is for eyes only: pipes and NO_COLOR get the plain line, instantly.
    if console.is_terminal and not console.no_color:
        try:
            with Live(
                _version_line(installed, 0),
                console=console,
                refresh_per_second=SPARKLE_FPS,
            ) as live:
                for frame in range(1, int(SPARKLE_SECONDS * SPARKLE_FPS)):
                    time.sleep(1 / SPARKLE_FPS)
                    live.update(_version_line(installed, frame))
        except KeyboardInterrupt:
            pass  # the sparkle is skippable; the version is already on screen
    else:
        click.echo(f"leek, version {installed}")


def _print_added(added: "Added") -> None:
    console = Console()
    details = " · ".join(
        part
        for part in (
            added.artist,
            str(added.year) if added.year else None,
            f"{added.tracks} tracks",
        )
        if part
    )
    console.print(
        Text.assemble(
            ("✓ ", f"bold {theme.GREEN}"),
            ("added ", theme.SUBTEXT0),
            (added.title, f"bold {theme.TEXT}"),
        )
    )
    console.print(Text(f"  {details}", style=theme.SUBTEXT1))
    console.print(
        Text.assemble(("  → ", theme.SUBTEXT0), (str(added.destination), theme.BLUE))
    )
    console.print(
        Text(f"  {added.claims} values read from the file tags", style=theme.SUBTEXT0)
    )


@leek.command()
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
def add(directory: Path) -> None:
    """Add one album to the library.

    The directory must hold exactly one album; for a tree of many,
    leek import will arrive later. Bad metadata never blocks: the
    album enters with whatever its tags claim.
    """
    # Imported here so a bare `leek` never pays the pipeline's startup cost.
    from leeks import library
    from leeks.detect import NotOneAlbum

    try:
        _print_added(library.add(directory))
    except (NotOneAlbum, library.AlreadyAdded) as refusal:
        raise click.ClickException(str(refusal)) from refusal


# The columns a listing prints when --fields is unset, in order. The names
# are attributes of the matching Listed* dataclass (library.py), so a value
# is a getattr away — the single typed seam every formatter reads (ADR 0014).
_DEFAULT_COLUMNS: dict[str, tuple[str, ...]] = {
    "albums": ("artist", "year", "title"),
    "tracks": ("artist", "album", "number", "title"),
    "artists": ("name",),
}

# Selectable handles beyond the default columns: names --fields accepts and
# `leek fields` lists, but that a listing does not show by default. id is the
# album's primary key, the handle `show id:N` names one entity by (ADR 0020) —
# discoverable here, not shelf furniture. The namespace grows (bitrate, path,
# …) as slices surface those facts (ADR 0018).
_SELECTABLE_EXTRAS: dict[str, tuple[str, ...]] = {"albums": ("id",)}


def _field_names(subject: str) -> tuple[str, ...]:
    """The full field namespace for a subject: default columns then extras."""
    return _DEFAULT_COLUMNS[subject] + _SELECTABLE_EXTRAS.get(subject, ())


def _display_cell(name: str, value: object) -> str:
    """Render one projected value as plain text for a pipe or a plain table.

    Absence is a rendering choice here, not data (ADR 0014): a missing artist
    shows the Unknown bucket (ADR 0010), every other missing field shows
    empty. Structured output (`--format json`) skips this and emits the typed
    value — null stays null.
    """
    if value is None:
        return "Unknown Artist" if name == "artist" else ""
    return str(value)


def _artist_cell(artist: str | None) -> Text:
    """The artist column, dim italic when it is the Unknown fallback (ADR 0010)."""
    if artist:
        return Text(artist)
    return Text("Unknown Artist", style=f"italic {theme.OVERLAY1}")


def _shelf_table(albums: "Sequence[Listed]") -> Table:
    shelf = Table(box=None, show_header=False, pad_edge=False)
    shelf.add_column(style=theme.TEXT)  # artist
    shelf.add_column(style=theme.SUBTEXT0, justify="right")  # year
    shelf.add_column(style=f"bold {theme.TEXT}")  # title
    for album in albums:
        shelf.add_row(
            _artist_cell(album.artist),
            _display_cell("year", album.year),
            album.title,
        )
    return shelf


def _track_table(tracks: "Sequence[ListedTrack]") -> Table:
    table = Table(box=None, show_header=False, pad_edge=False)
    table.add_column(style=theme.TEXT)  # artist
    table.add_column(style=theme.SUBTEXT0)  # album
    table.add_column(style=theme.SUBTEXT0, justify="right")  # number
    table.add_column(style=f"bold {theme.TEXT}")  # title
    for track in tracks:
        table.add_row(
            _artist_cell(track.artist),
            track.album,
            _display_cell("number", track.number),
            track.title,
        )
    return table


def _artist_table(artists: "Sequence[ListedArtist]") -> Table:
    table = Table(box=None, show_header=False, pad_edge=False)
    table.add_column(style=theme.TEXT)
    for artist in artists:
        table.add_row(artist.name)
    return table


def _parse_fields(subject: str, spec: str) -> tuple[str, ...]:
    """The `--fields` names, validated against the subject's namespace.

    Selection, not interpolation (ADR 0016): a comma-separated list of
    names, trimmed of surrounding whitespace. An unknown name is a loud
    usage error listing the valid names for the subject — never a silent
    skip — so the exit code is non-zero. Duplicates are harmless and kept
    as given; field order is column order.
    """
    valid = _field_names(subject)
    names = tuple(name.strip() for name in spec.split(","))
    for name in names:
        if not name:
            raise click.BadParameter(
                f"empty field name (a stray comma?); choose from {', '.join(valid)}",
                param_hint="--fields",
            )
        if name not in valid:
            raise click.BadParameter(
                f"{name!r} is not a field of {subject}; choose from {', '.join(valid)}",
                param_hint="--fields",
            )
    return names


def _plain_table(rows: Sequence[Any], fields: Sequence[str]) -> Table:
    """A utilitarian table for `--fields`: one column per selected field.

    No per-field styling (ADR 0016) — the curated styled tables (the
    italic Unknown bucket, bold titles) are only the default view. This
    matches the headerless house style; a header row is a deferred
    question (ADR 0016). Values come off the typed projection via getattr
    and `_display_cell`, the same seam the pipe reads (ADR 0014).
    """
    table = Table(box=None, show_header=False, pad_edge=False)
    for _ in fields:
        table.add_column(style=theme.TEXT)
    for row in rows:
        table.add_row(*(_display_cell(name, getattr(row, name)) for name in fields))
    return table


def _emit_json(rows: Sequence[Any], columns: Sequence[str]) -> None:
    """Emit the listing as JSON: an array of objects, keyed by `columns`.

    Renders the typed projection directly (ADR 0014/0017) — values come off
    each row by getattr and are NOT passed through `_display_cell`, so a year
    is a JSON number and a genuine absence is JSON `null`, never the Unknown
    bucket fallback the human formatters supply. JSON ignores the isatty
    split: a script asked for this shape, so it gets it onto a terminal or a
    pipe alike.

    Punts (decision altitude, ADR 0017): the envelope is a top-level array of
    objects (vs. JSON Lines) and the output is indented for the eye (jq
    reformats anyway) — grammar deferred to contact. An empty listing emits
    `[]`, not the human stderr note, so a machine consumer always parses valid
    JSON (and an empty result is a clean exit 0, not an error).
    """
    payload = [{name: getattr(row, name) for name in columns} for row in rows]
    click.echo(json.dumps(payload, indent=2))


def _emit(
    rows: Sequence[Any],
    *,
    subject: str,
    table: Callable[..., Table],
    note: str,
    fields: tuple[str, ...] | None = None,
    output_format: str | None = None,
) -> None:
    """Print a listing, or its absence: the shape every `list` subject shares.

    An empty result is a note on stderr (exit 0) so stdout stays a clean
    list. The default `human` shape adapts to the stream, not the format: a
    terminal gets the themed, aligned table; a pipe gets the same fields as
    bare plain lines — no colour, no alignment (ADR 0019). The test is the
    stream's own isatty, not Console.is_terminal, which reports True under
    FORCE_COLOR even into a pipe.

    The piped line is the subject's fields (`_FIELDS`) read off each row,
    rendered with `_display_cell` and space-joined, absent values dropped —
    the typed projection stringified at the edge (ADR 0014). It is for
    reading, never a parse target; a machine consumer asks for `--format
    json` (ADR 0019).

    `--fields` (when given) selects which fields print and in what order,
    replacing the curated default columns (ADR 0016): the piped lines and
    the TTY's plain, unstyled table both read exactly those.

    `--format` names the output shape and is orthogonal to `--fields` (ADR
    0017). `human` is the default and takes the isatty split above; a
    structured shape like `json` bypasses the split and replaces the human
    formatters, keying on the same resolved column list. Only `human` and
    `json` exist today; `csv` and `tsv` are deferred until the slice arrives.
    """
    columns = fields if fields is not None else _DEFAULT_COLUMNS[subject]
    if output_format == "json":
        _emit_json(rows, columns)
        return
    if not rows:
        Console(stderr=True).print(Text(note, style=theme.SUBTEXT0))
        return
    if not sys.stdout.isatty():
        for row in rows:
            cells = (_display_cell(name, getattr(row, name)) for name in columns)
            click.echo(" ".join(cell for cell in cells if cell))
        return
    Console().print(_plain_table(rows, fields) if fields is not None else table(rows))


@leek.command(name="list")
@click.argument("terms", nargs=-1)
@click.option(
    "--albums",
    "subject",
    flag_value="albums",
    default=True,
    help="List albums (default).",
)
@click.option("--tracks", "subject", flag_value="tracks", help="List tracks.")
@click.option("--artists", "subject", flag_value="artists", help="List artists.")
@click.option(
    "--fields",
    "fields_spec",
    default=None,
    help="Print only these fields, in order, e.g. artist,title.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["human", "json"]),
    default="human",
    help="Output shape: human (default) or json.",
)
def list_command(
    terms: tuple[str, ...],
    subject: str,
    fields_spec: str | None,
    output_format: str | None,
) -> None:
    """List the library, in shelf order, albums by default.

    Terms narrow the listing: an album stays only when it matches all of
    them. --albums, --tracks, and --artists choose what to list, one at a
    time; with none, you get albums. --fields picks which fields to print,
    in place of the usual columns. --format names the output shape: human
    (the default) or json.
    """
    # --fields and --format are orthogonal: --format keys on the same
    # fields --fields resolves, so the two compose (ADRs 0016, 0017).
    # Imported here so a bare `leek` never pays the pipeline's startup cost.
    from leeks import library

    fields = _parse_fields(subject, fields_spec) if fields_spec is not None else None

    if subject == "tracks":
        _emit(
            library.list_tracks(terms),
            subject="tracks",
            table=_track_table,
            note="no tracks match that"
            if terms
            else "the library is empty, leek add brings music in",
            fields=fields,
            output_format=output_format,
        )
    elif subject == "artists":
        _emit(
            library.list_artists(terms),
            subject="artists",
            table=_artist_table,
            note="no artists match that" if terms else "no artists yet",
            fields=fields,
            output_format=output_format,
        )
    else:
        _emit(
            library.list_albums(terms),
            subject="albums",
            table=_shelf_table,
            note="nothing on the shelf matches that"
            if terms
            else "the library is empty, leek add brings music in",
            fields=fields,
            output_format=output_format,
        )


def _duration(seconds: float | None) -> str:
    """Seconds as m:ss, or empty when the duration was not decoded."""
    if seconds is None:
        return ""
    total = round(seconds)
    return f"{total // 60}:{total % 60:02d}"


def _bitrate(bitrate: int | None) -> str:
    """Bits per second as kbps (an ADR 0007 measurement), or empty when unknown."""
    if bitrate is None:
        return ""
    return f"{bitrate // 1000} kbps"


def _album_heading(album: "ShownAlbum") -> Text:
    """`<artist> — <title> (<year>)`, the Unknown bucket styled (ADR 0010)."""
    heading = _artist_cell(album.artist)  # a fresh Text, safe to append to
    heading.append(" — ", style=theme.SUBTEXT0)
    heading.append(album.title, style=f"bold {theme.TEXT}")
    if album.year is not None:
        heading.append(f" ({album.year})", style=theme.SUBTEXT0)
    return heading


def _measurements_table(tracks: "Sequence[ShownTrack]") -> Table:
    """The depth view's track list: number, title, and each file's measurements."""
    table = Table(box=None, show_header=False, pad_edge=False)
    table.add_column(style=theme.SUBTEXT0, justify="right")  # number
    table.add_column(style=theme.TEXT)  # title
    table.add_column(style=theme.SUBTEXT0, justify="right")  # duration
    table.add_column(style=theme.SUBTEXT0)  # format
    table.add_column(style=theme.SUBTEXT0, justify="right")  # bitrate
    for track in tracks:
        # One file per track today; multi-file nesting is deferred (ADR 0020).
        file: ShownFile | None = track.files[0] if track.files else None
        table.add_row(
            str(track.number) if track.number is not None else "",
            track.title,
            _duration(file.duration) if file else "",
            file.format if file else "",
            _bitrate(file.bitrate) if file else "",
        )
    return table


def _claims_table(claims: "Sequence[Claim]") -> Table:
    """The claim layer (ADR 0008): field, value, and the source that claimed it."""
    table = Table(box=None, show_header=False, pad_edge=False, padding=(0, 3, 0, 0))
    table.add_column(style=theme.SUBTEXT0)  # field
    table.add_column(style=theme.TEXT)  # value
    table.add_column(style=theme.OVERLAY1)  # source
    for claim in claims:
        table.add_row(claim.field, claim.value, claim.source)
    return table


def _print_album(console: Console, album: "ShownAlbum", *, with_sources: bool) -> None:
    """One album in depth: the merged heading, its genres, then tracks or claims."""
    console.print(_album_heading(album))
    if album.genres:
        console.print(Text("  " + ", ".join(album.genres), style=theme.SUBTEXT0))
    console.print()
    # expand=False keeps the indent without padding rows to the console width —
    # the width-alignment a pipe must not carry (ADR 0019).
    if not with_sources:
        console.print(
            Padding(_measurements_table(album.tracks), (0, 0, 0, 2), expand=False)
        )
        return
    # --sources unfolds the claim layer: album fields, then each track (ADR 0020).
    console.print(Text("  album", style=theme.SUBTEXT1))
    console.print(Padding(_claims_table(album.claims), (0, 0, 0, 4), expand=False))
    for track in album.tracks:
        number = f"{track.number}  " if track.number is not None else ""
        console.print(
            Padding(
                Text(f"{number}{track.title}", style=theme.TEXT),
                (1, 0, 0, 2),
                expand=False,
            )
        )
        console.print(Padding(_claims_table(track.claims), (0, 0, 0, 4), expand=False))


def _show_json(albums: "Sequence[ShownAlbum]") -> None:
    """The depth projection as JSON: an array of nested album objects.

    Always an array, one element per match, and always full — claims included
    regardless of --sources (ADRs 0017/0019/0020). asdict walks the frozen
    projection (ADR 0014), so years stay ints, durations floats, and genuine
    absence stays null. Like list's JSON it ignores the isatty split: a script
    asked for this shape, so it lands on a terminal or a pipe alike.
    """
    click.echo(json.dumps([asdict(album) for album in albums], indent=2))


@leek.command(name="show")
@click.argument("terms", nargs=-1)
@click.option(
    "--sources",
    "-s",
    "with_sources",
    is_flag=True,
    help="Unfold the claim layer: who claimed each field.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json"]),
    default=None,
    help="Print machine-readable output instead, e.g. json.",
)
def show_command(
    terms: tuple[str, ...], with_sources: bool, output_format: str | None
) -> None:
    """Show an album in depth — its tracks, their files, and on request its sources.

    Terms pick the album the way leek list does — by artist, title, or
    year — or id:N names one exactly. A unique match is shown in full; when
    several match, all of them are (a chooser to narrow them comes later).
    --sources unfolds the claim layer beneath each field. --format json
    prints the whole projection, always as an array.
    """
    # Imported here so a bare `leek` never pays the pipeline's startup cost.
    from leeks import library

    albums = library.show_albums(terms)
    if output_format == "json":
        _show_json(albums)
        return
    if not albums:
        note = (
            "nothing matches that"
            if terms
            else "the library is empty, leek add brings music in"
        )
        Console(stderr=True).print(Text(note, style=theme.SUBTEXT0))
        return
    console = Console()
    for index, album in enumerate(albums):
        if index:
            console.print()  # a blank line between albums when several match
        _print_album(console, album, with_sources=with_sources)


@leek.command(name="fields")
@click.option(
    "--albums",
    "subject",
    flag_value="albums",
    default=True,
    help="Fields of albums (default).",
)
@click.option("--tracks", "subject", flag_value="tracks", help="Fields of tracks.")
@click.option("--artists", "subject", flag_value="artists", help="Fields of artists.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["human", "json"]),
    default="human",
    help="Output shape: human (default) or json.",
)
def fields_command(subject: str, output_format: str | None) -> None:
    """Show the fields a subject exposes, the names `leek list --fields` can use.

    --albums, --tracks, and --artists choose the subject, one at a time;
    with none, the subject is albums. The names print one per line, or as
    a JSON array with --format json. They are exactly the names --fields
    accepts for that subject.
    """
    # The discovery side of --fields (ADR 0018), reading the same namespace
    # --fields validates against (ADR 0016) so the two can never disagree.
    # --format json mirrors list's structured shape (ADR 0017). No library
    # import: the namespace is static, so `leek fields` never touches the
    # database and pays no pipeline startup cost.
    names = _field_names(subject)
    if output_format == "json":
        click.echo(json.dumps(list(names)))
        return
    for name in names:
        click.echo(name)


@leek.command(name="help")
@click.pass_context
def help_command(ctx: click.Context) -> None:
    """Show help for leek."""
    assert ctx.parent is not None  # always invoked as a subcommand of leek
    # color=True: rich already decided colour when rendering; echo must not re-strip it.
    click.echo(ctx.parent.get_help(), color=True)
