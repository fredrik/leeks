"""The leek command-line interface."""

import rich_click as click

from leeks import theme

theme.apply()


# invoke_without_command: click's default no_args_is_help exits with code 2;
# a bare `leek` should greet with help and exit 0.
@click.group(invoke_without_command=True)
@click.version_option(package_name="leeks")
@click.pass_context
def leek(ctx: click.Context) -> None:
    """A music library organiser, and the spiritual successor to beets."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
