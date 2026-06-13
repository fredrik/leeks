"""The leek command-line interface."""

import importlib.metadata
import json
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

import rich_click as click
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from leeks import theme

if TYPE_CHECKING:
    from leeks.library import Added, Listed, ListedArtist, ListedTrack

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
            (" — a music library organiser", f"bold {theme.TEXT}"),
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
        Text(f"  {added.claims} claims recorded from file tags", style=theme.SUBTEXT0)
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


# The renderable fields each subject projects, in column order. The names
# are attributes of the matching Listed* dataclass (library.py), so a value
# is a getattr away — the single typed seam every formatter reads (ADR 0014).
# Today's namespace is the display columns; it grows (bitrate, path, …) when a
# slice surfaces those facts, and `leek fields` reports it (ADR 0018).
_FIELDS: dict[str, tuple[str, ...]] = {
    "albums": ("artist", "year", "title"),
    "tracks": ("artist", "album", "number", "title"),
    "artists": ("name",),
}


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
    valid = _FIELDS[subject]
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
    list. The themed table is for eyes only — it wraps long rows at the
    console width, and a record folded across lines breaks `leek list |
    grep`; a pipe gets one tab-separated record per row instead (ADR 0011).
    The test is the stream's own isatty, not Console.is_terminal, which
    reports True under FORCE_COLOR even into a pipe, which would wrap.

    The pipe record is the subject's fields (`_FIELDS`) read off each row and
    rendered with `_display_cell` — the typed projection, stringified at the
    edge (ADR 0014).

    `--fields` (when given) selects which fields print and in what order,
    replacing the curated default columns (ADR 0016): the pipe records and
    the TTY's plain, unstyled table both read exactly those.

    `--format` (when given) names an explicit structured shape and is
    orthogonal to `--fields` (ADR 0017): it keys on the same resolved column
    list, bypasses the isatty split, and replaces the human formatters. Only
    `json` exists today; `csv` is deferred until the slice arrives.
    """
    columns = fields if fields is not None else _FIELDS[subject]
    if output_format == "json":
        _emit_json(rows, columns)
        return
    if not rows:
        Console(stderr=True).print(Text(note, style=theme.SUBTEXT0))
        return
    if not sys.stdout.isatty():
        for row in rows:
            click.echo(
                "\t".join(_display_cell(name, getattr(row, name)) for name in columns)
            )
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
    type=click.Choice(["json"]),
    default=None,
    help="Print machine-readable output instead, e.g. json.",
)
def list_command(
    terms: tuple[str, ...],
    subject: str,
    fields_spec: str | None,
    output_format: str | None,
) -> None:
    """List the library, in shelf order — albums by default.

    Terms narrow the listing: an album stays only when it matches all of
    them. --albums, --tracks, and --artists choose what to list, one at a
    time; with none, you get albums. --fields picks which fields to print,
    in place of the usual columns. --format prints machine-readable output
    instead, e.g. --format json.
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
            else "the library is empty — leek add brings music in",
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
            else "the library is empty — leek add brings music in",
            fields=fields,
            output_format=output_format,
        )


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
    type=click.Choice(["json"]),
    default=None,
    help="Print machine-readable output instead, e.g. json.",
)
def fields_command(subject: str, output_format: str | None) -> None:
    """Show the fields a subject exposes, the names `leek list --fields` can use.

    --albums, --tracks, and --artists choose the subject, one at a time;
    with none, the subject is albums. The names print one per line, or as
    a JSON array with --format json. They are exactly the names --fields
    accepts for that subject.
    """
    # The discovery side of --fields (ADR 0018), reading the same _FIELDS
    # map --fields validates against (ADR 0016) so the two can never
    # disagree. --format json mirrors list's structured shape (ADR 0017).
    # No library import: the namespace is static, so `leek fields` never
    # touches the database and pays no pipeline startup cost.
    names = _FIELDS[subject]
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
