"""The leek command-line interface."""

import importlib.metadata
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
# slice surfaces those facts, and `leek fields` will report it (ADR 0018).
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


def _emit(
    rows: Sequence[Any],
    *,
    subject: str,
    table: Callable[..., Table],
    note: str,
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
    """
    if not rows:
        Console(stderr=True).print(Text(note, style=theme.SUBTEXT0))
        return
    if not sys.stdout.isatty():
        fields = _FIELDS[subject]
        for row in rows:
            click.echo(
                "\t".join(_display_cell(name, getattr(row, name)) for name in fields)
            )
        return
    Console().print(table(rows))


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
def list_command(terms: tuple[str, ...], subject: str) -> None:
    """List the library, in shelf order — albums by default.

    Terms narrow the listing: an item stays only when every term
    matches. --albums, --tracks, and --artists choose the subject (one
    at a time); with none, the subject is albums.
    """
    # Imported here so a bare `leek` never pays the pipeline's startup cost.
    from leeks import library

    if subject == "tracks":
        _emit(
            library.list_tracks(terms),
            subject="tracks",
            table=_track_table,
            note="no tracks match that"
            if terms
            else "the library is empty — leek add brings music in",
        )
    elif subject == "artists":
        _emit(
            library.list_artists(terms),
            subject="artists",
            table=_artist_table,
            note="no artists match that" if terms else "no artists yet",
        )
    else:
        _emit(
            library.list_albums(terms),
            subject="albums",
            table=_shelf_table,
            note="nothing on the shelf matches that"
            if terms
            else "the library is empty — leek add brings music in",
        )


@leek.command(name="help")
@click.pass_context
def help_command(ctx: click.Context) -> None:
    """Show help for leek."""
    assert ctx.parent is not None  # always invoked as a subcommand of leek
    # color=True: rich already decided colour when rendering; echo must not re-strip it.
    click.echo(ctx.parent.get_help(), color=True)
