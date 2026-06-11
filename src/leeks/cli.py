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


def _version_line(version: str, offset: int) -> Text:
    return Text.assemble(
        theme.rainbow("leek", offset), (f", version {version}", theme.TEXT)
    )


def _show_version(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return
    version = importlib.metadata.version("leeks")
    console = Console()
    # The sparkle is for eyes only: pipes and NO_COLOR get the plain line, instantly.
    if console.is_terminal and not console.no_color:
        try:
            with Live(
                _version_line(version, 0),
                console=console,
                refresh_per_second=SPARKLE_FPS,
            ) as live:
                for frame in range(1, int(SPARKLE_SECONDS * SPARKLE_FPS)):
                    time.sleep(1 / SPARKLE_FPS)
                    live.update(_version_line(version, frame))
        except KeyboardInterrupt:
            pass  # the sparkle is skippable; the version is already on screen
    else:
        click.echo(f"leek, version {version}")
    ctx.exit()


# invoke_without_command: click's default no_args_is_help exits with code 2;
# a bare `leek` should greet with help and exit 0.
@click.group(invoke_without_command=True)
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_show_version,
    help="Show the version and exit.",
)
@click.pass_context
def leek(ctx: click.Context) -> None:
    """A music library organiser, and the spiritual successor to beets."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
