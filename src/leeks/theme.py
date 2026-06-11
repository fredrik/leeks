"""The leeks look: Catppuccin Mocha.

Palette reference: https://catppuccin.com/palette. Styles are truecolor;
rich downgrades them automatically on less capable terminals and drops
them entirely when output is piped or NO_COLOR is set.
"""

import rich_click.rich_click as rc
from rich.text import Text

# Accents
ROSEWATER = "#f5e0dc"
FLAMINGO = "#f2cdcd"
PINK = "#f5c2e7"
MAUVE = "#cba6f7"
RED = "#f38ba8"
MAROON = "#eba0ac"
PEACH = "#fab387"
YELLOW = "#f9e2af"
GREEN = "#a6e3a1"
TEAL = "#94e2d5"
SKY = "#89dceb"
SAPPHIRE = "#74c7ec"
BLUE = "#89b4fa"
LAVENDER = "#b4befe"

# Text
TEXT = "#cdd6f4"
SUBTEXT1 = "#bac2de"
SUBTEXT0 = "#a6adc8"

# Overlays and surfaces
OVERLAY2 = "#9399b2"
OVERLAY1 = "#7f849c"
OVERLAY0 = "#6c7086"
SURFACE2 = "#585b70"
SURFACE1 = "#45475a"
SURFACE0 = "#313244"


# The accent cycle for rainbow sparkle, in spectral order.
RAINBOW = [RED, PEACH, YELLOW, GREEN, SAPPHIRE, MAUVE]


def rainbow(text: str, offset: int = 0) -> Text:
    """Colour each character from the accent cycle, starting at offset."""
    out = Text()
    for i, char in enumerate(text):
        out.append(char, style=f"bold {RAINBOW[(i + offset) % len(RAINBOW)]}")
    return out


def apply() -> None:
    """Dress rich-click's help rendering in Mocha."""
    rc.STYLE_USAGE = f"bold {MAUVE}"
    rc.STYLE_USAGE_COMMAND = f"bold {TEXT}"
    rc.STYLE_COMMAND = f"bold {MAUVE}"
    rc.STYLE_OPTION = f"bold {BLUE}"
    rc.STYLE_SWITCH = f"bold {GREEN}"
    rc.STYLE_ARGUMENT = f"bold {TEAL}"
    rc.STYLE_METAVAR = PEACH
    rc.STYLE_METAVAR_SEPARATOR = OVERLAY0
    rc.STYLE_HELPTEXT_FIRST_LINE = TEXT
    rc.STYLE_HELPTEXT = SUBTEXT0
    rc.STYLE_OPTION_HELP = SUBTEXT1
    rc.STYLE_OPTION_DEFAULT = OVERLAY1
    rc.STYLE_OPTION_ENVVAR = OVERLAY1
    rc.STYLE_REQUIRED_SHORT = f"bold {RED}"
    rc.STYLE_REQUIRED_LONG = f"dim {RED}"
    rc.STYLE_OPTIONS_PANEL_BORDER = SURFACE2
    rc.STYLE_COMMANDS_PANEL_BORDER = SURFACE2
    rc.STYLE_ERRORS_PANEL_BORDER = RED
    rc.STYLE_ERRORS_SUGGESTION = SUBTEXT0
    rc.STYLE_DEPRECATED = YELLOW
    rc.STYLE_ABORTED = f"bold {RED}"
