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


def _shelf_fields(album: "Listed") -> tuple[str, str, str, str]:
    """Artist, year, title, track count: the four columns of the shelf."""
    return (
        album.artist or "Unknown Artist",
        str(album.year) if album.year else "",
        album.title,
        f"{album.tracks} track" if album.tracks == 1 else f"{album.tracks} tracks",
    )


def _track_fields(track: "ListedTrack") -> tuple[str, str, str, str]:
    """Number, title, artist, album: the four columns of a track row."""
    return (
        str(track.number) if track.number is not None else "",
        track.title,
        track.artist or "Unknown Artist",
        track.album,
    )


def _artist_fields(artist: "ListedArtist") -> tuple[str]:
    """The single column of an artist row: the name."""
    return (artist.name,)


def _artist_cell(artist: str | None) -> Text:
    """The artist column, dim italic when it is the Unknown fallback (ADR 0010)."""
    if artist:
        return Text(artist)
    return Text("Unknown Artist", style=f"italic {theme.OVERLAY1}")


def _shelf_table(albums: "Sequence[Listed]") -> Table:
    shelf = Table(box=None, show_header=False, pad_edge=False)
    shelf.add_column(style=theme.TEXT)
    shelf.add_column(style=theme.SUBTEXT0, justify="right")
    shelf.add_column(style=f"bold {theme.TEXT}")
    shelf.add_column(style=theme.SUBTEXT0)
    for album in albums:
        _, year, title, tracks = _shelf_fields(album)
        shelf.add_row(_artist_cell(album.artist), year, title, tracks)
    return shelf


def _track_table(tracks: "Sequence[ListedTrack]") -> Table:
    table = Table(box=None, show_header=False, pad_edge=False)
    table.add_column(style=theme.SUBTEXT0, justify="right")  # number
    table.add_column(style=f"bold {theme.TEXT}")  # title
    table.add_column(style=theme.TEXT)  # artist
    table.add_column(style=theme.SUBTEXT0)  # album
    for track in tracks:
        number, title, _, album = _track_fields(track)
        table.add_row(number, title, _artist_cell(track.artist), album)
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
    record: Callable[..., tuple[str, ...]],
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
    """
    if not rows:
        Console(stderr=True).print(Text(note, style=theme.SUBTEXT0))
        return
    if not sys.stdout.isatty():
        for row in rows:
            click.echo("\t".join(record(row)))
        return
    Console().print(table(rows))


@leek.command(name="list")
@click.argument("terms", nargs=-1)
@click.option(
    "--tracks", "subject", flag_value="tracks", help="List tracks, not albums."
)
@click.option(
    "--artists", "subject", flag_value="artists", help="List artists, not albums."
)
def list_command(terms: tuple[str, ...], subject: str | None) -> None:
    """List the library, in shelf order — albums by default.

    Terms narrow the listing: an item stays only when every term
    matches. --tracks and --artists list those entities instead (one
    subject at a time); with neither, the subject is albums.
    """
    # Imported here so a bare `leek` never pays the pipeline's startup cost.
    from leeks import library

    if subject == "tracks":
        _emit(
            library.list_tracks(terms),
            record=_track_fields,
            table=_track_table,
            note="no tracks match that"
            if terms
            else "the library is empty — leek add brings music in",
        )
    elif subject == "artists":
        _emit(
            library.list_artists(terms),
            record=_artist_fields,
            table=_artist_table,
            note="no artists match that" if terms else "no artists yet",
        )
    else:
        _emit(
            library.list_albums(terms),
            record=_shelf_fields,
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
