"""The leek command-line interface."""

import importlib.metadata
import time

import rich_click as click
from rich.console import Console
from rich.live import Live
from rich.text import Text

from leeks import theme

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


@leek.command(name="help")
@click.pass_context
def help_command(ctx: click.Context) -> None:
    """Show help for leek."""
    assert ctx.parent is not None  # always invoked as a subcommand of leek
    # color=True: rich already decided colour when rendering; echo must not re-strip it.
    click.echo(ctx.parent.get_help(), color=True)
