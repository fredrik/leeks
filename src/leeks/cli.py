"""The leek command-line interface."""

import importlib.metadata
import time
from pathlib import Path
from typing import TYPE_CHECKING

import rich_click as click
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from leeks import theme

if TYPE_CHECKING:
    from leeks.library import Added, Listed

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


@leek.command(name="list")
@click.argument("terms", nargs=-1)
def list_command(terms: tuple[str, ...]) -> None:
    """List the library's albums, in shelf order.

    Terms narrow the shelf: an album stays only when every term
    appears in its artist, title, or year. No terms lists everything.
    """
    # Imported here so a bare `leek` never pays the pipeline's startup cost.
    from leeks import library

    albums = library.list_albums(terms)
    if not albums:
        note = (
            "nothing on the shelf matches that"
            if terms
            else "the library is empty — leek add brings music in"
        )
        # Notes go to stderr: stdout stays a clean list of albums.
        Console(stderr=True).print(Text(note, style=theme.SUBTEXT0))
        return
    console = Console()
    # The table is for eyes only: it wraps long rows at the console
    # width, and a record folded across lines breaks `leek list | grep`.
    # Pipes get one tab-separated record per album (ADR 0011).
    if not console.is_terminal:
        for album in albums:
            click.echo("\t".join(_shelf_fields(album)))
        return
    shelf = Table(box=None, show_header=False, pad_edge=False)
    shelf.add_column(style=theme.TEXT)
    shelf.add_column(style=theme.SUBTEXT0, justify="right")
    shelf.add_column(style=f"bold {theme.TEXT}")
    shelf.add_column(style=theme.SUBTEXT0)
    for album in albums:
        artist, year, title, tracks = _shelf_fields(album)
        styled = (
            Text(artist)
            if album.artist
            # The bucket, visibly a fallback and not data (ADR 0010).
            else Text(artist, style=f"italic {theme.OVERLAY1}")
        )
        shelf.add_row(styled, year, title, tracks)
    console.print(shelf)


@leek.command(name="help")
@click.pass_context
def help_command(ctx: click.Context) -> None:
    """Show help for leek."""
    assert ctx.parent is not None  # always invoked as a subcommand of leek
    # color=True: rich already decided colour when rendering; echo must not re-strip it.
    click.echo(ctx.parent.get_help(), color=True)
