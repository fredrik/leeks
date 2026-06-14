"""The leeks look: a small set of selectable themes.

A theme is a *role → style* map, never colour names on the loose. The views and
the help text read roles (``theme.ARTIST``, ``theme.MUTED``), so they never know
what colour the artist is — only that it is the artist. Each theme answers that
question its own way: Mocha makes the artist mauve, Gruvbox makes it purple, and
the colour names that decide so live as locals inside each builder, never as a
public slot (ADR 0028). That is what keeps the names honest — there is no
"mauve" slot a green theme would have to lie into.

``LEEKS_THEME`` picks the theme at startup; the default is Mocha (ADR 0002).
Styles are truecolor; rich downgrades them on less capable terminals and drops
them when output is piped or NO_COLOR is set.
"""

import os
from dataclasses import dataclass, fields

import rich_click.rich_click as rc
from rich.text import Text


@dataclass(frozen=True)
class Theme:
    """A complete binding of leeks' style roles to concrete rich styles.

    Every field is a full rich style string (it may carry ``bold``/``italic``),
    so a consumer assigns it straight through and never composes on top of it.
    The content roles (artist, title, album, year, genre) carry the distinct
    hues the field vocabulary needs (ADR 0024); the rest are text tiers and
    chrome. A new theme is a new ``Theme`` and nothing else.
    """

    # Content vocabulary — the distinct hues a field is read by (ADR 0024).
    artist: str
    title: str
    album: str
    year: str
    genre: str
    # Structural fields within a view.
    number: str
    measure: str
    claim_field: str
    source: str
    label: str
    unknown: str
    path: str
    # Text tiers, brightest to faintest.
    body: str
    muted: str
    faint: str
    border: str
    # Semantic accents and help chrome.
    success: str
    link: str
    error: str
    warning: str
    # The rainbow sparkle cycle, in spectral order.
    rainbow: tuple[str, ...]


def _mocha() -> Theme:
    # Catppuccin Mocha — the default (ADR 0002), a dark pastel.
    mauve, sapphire, peach = "#cba6f7", "#74c7ec", "#fab387"
    green, blue = "#a6e3a1", "#89b4fa"
    text, subtext1, subtext0 = "#cdd6f4", "#bac2de", "#a6adc8"
    overlay1, surface2 = "#7f849c", "#585b70"
    red, yellow = "#f38ba8", "#f9e2af"
    return Theme(
        artist=f"bold {mauve}",
        title=f"bold {text}",
        album=sapphire,
        year=peach,
        genre=green,
        number=subtext0,
        measure=subtext0,
        claim_field=subtext0,
        source=overlay1,
        label=subtext1,
        unknown=f"italic {overlay1}",
        path=blue,
        body=text,
        muted=subtext0,
        faint=overlay1,
        border=surface2,
        success=f"bold {green}",
        link=f"bold {blue}",
        error=f"bold {red}",
        warning=yellow,
        rainbow=(red, peach, yellow, green, sapphire, mauve),
    )


def _latte() -> Theme:
    # Catppuccin Latte — Mocha's light sibling, the same hues over a light base.
    mauve, sapphire, peach = "#8839ef", "#209fb5", "#fe640b"
    green, blue = "#40a02b", "#1e66f5"
    text, subtext1, subtext0 = "#4c4f69", "#5c5f77", "#6c6f85"
    overlay1, surface2 = "#8c8fa1", "#acb0be"
    red, yellow = "#d20f39", "#df8e1d"
    return Theme(
        artist=f"bold {mauve}",
        title=f"bold {text}",
        album=sapphire,
        year=peach,
        genre=green,
        number=subtext0,
        measure=subtext0,
        claim_field=subtext0,
        source=overlay1,
        label=subtext1,
        unknown=f"italic {overlay1}",
        path=blue,
        body=text,
        muted=subtext0,
        faint=overlay1,
        border=surface2,
        success=f"bold {green}",
        link=f"bold {blue}",
        error=f"bold {red}",
        warning=yellow,
        rainbow=(red, peach, yellow, green, sapphire, mauve),
    )


def _gruvbox() -> Theme:
    # Gruvbox — something entirely different: warm, earthy, retro. The artist's
    # accent is Gruvbox purple; year is its orange, album its aqua.
    purple, aqua, orange = "#d3869b", "#8ec07c", "#fe8019"
    green, blue = "#b8bb26", "#83a598"
    fg, fg2, fg3 = "#ebdbb2", "#d5c4a1", "#bdae93"
    gray, bg4 = "#928374", "#7c6f64"
    red, yellow = "#fb4934", "#fabd2f"
    return Theme(
        artist=f"bold {purple}",
        title=f"bold {fg}",
        album=aqua,
        year=orange,
        genre=green,
        number=fg3,
        measure=fg3,
        claim_field=fg3,
        source=gray,
        label=fg2,
        unknown=f"italic {gray}",
        path=blue,
        body=fg,
        muted=fg3,
        faint=gray,
        border=bg4,
        success=f"bold {green}",
        link=f"bold {blue}",
        error=f"bold {red}",
        warning=yellow,
        rainbow=(red, orange, yellow, green, aqua, purple),
    )


THEMES: dict[str, Theme] = {
    "mocha": _mocha(),
    "latte": _latte(),
    "gruvbox": _gruvbox(),
}
DEFAULT = "mocha"


def _select(name: str | None) -> Theme:
    """The theme LEEKS_THEME names, or Mocha when it is unset or unknown.

    An unknown name falls back rather than failing: a misremembered theme still
    leaves leek usable, just in the default dress (ADR 0028).
    """
    if name is None:
        return THEMES[DEFAULT]
    return THEMES.get(name.strip().lower(), THEMES[DEFAULT])


# Resolved once at import: LEEKS_THEME is a startup choice, not a live switch.
ACTIVE = _select(os.environ.get("LEEKS_THEME"))

# The active theme's roles, as module constants the views read by name. Only the
# roles the views use are surfaced here; the help chrome (faint, border, error,
# warning) is read from ACTIVE by apply() below.
ARTIST = ACTIVE.artist
TITLE = ACTIVE.title
ALBUM = ACTIVE.album
YEAR = ACTIVE.year
GENRE = ACTIVE.genre
NUMBER = ACTIVE.number
MEASURE = ACTIVE.measure
CLAIM_FIELD = ACTIVE.claim_field
SOURCE = ACTIVE.source
LABEL = ACTIVE.label
UNKNOWN = ACTIVE.unknown
PATH = ACTIVE.path
BODY = ACTIVE.body
MUTED = ACTIVE.muted
SUCCESS = ACTIVE.success
LINK = ACTIVE.link

# The sparkle cycle of the active theme (a tuple of bare colours).
RAINBOW = ACTIVE.rainbow


def rainbow(text: str, offset: int = 0) -> Text:
    """Colour each character from the active theme's accent cycle, from offset."""
    out = Text()
    for i, char in enumerate(text):
        out.append(char, style=f"bold {RAINBOW[(i + offset) % len(RAINBOW)]}")
    return out


def apply() -> None:
    """Dress rich-click's help rendering in the active theme, by role (ADR 0028)."""
    rc.STYLE_USAGE = ACTIVE.artist
    rc.STYLE_USAGE_COMMAND = ACTIVE.title
    rc.STYLE_COMMAND = ACTIVE.artist
    rc.STYLE_OPTION = ACTIVE.link
    rc.STYLE_SWITCH = ACTIVE.success
    rc.STYLE_ARGUMENT = ACTIVE.album
    rc.STYLE_METAVAR = ACTIVE.year
    rc.STYLE_METAVAR_SEPARATOR = ACTIVE.faint
    rc.STYLE_HELPTEXT_FIRST_LINE = ACTIVE.body
    rc.STYLE_HELPTEXT = ACTIVE.muted
    rc.STYLE_OPTION_HELP = ACTIVE.label
    rc.STYLE_OPTION_DEFAULT = ACTIVE.faint
    rc.STYLE_OPTION_ENVVAR = ACTIVE.faint
    rc.STYLE_REQUIRED_SHORT = ACTIVE.error
    rc.STYLE_REQUIRED_LONG = ACTIVE.error
    rc.STYLE_OPTIONS_PANEL_BORDER = ACTIVE.border
    rc.STYLE_COMMANDS_PANEL_BORDER = ACTIVE.border
    rc.STYLE_ERRORS_PANEL_BORDER = ACTIVE.error
    rc.STYLE_ERRORS_SUGGESTION = ACTIVE.muted
    rc.STYLE_DEPRECATED = ACTIVE.warning
    rc.STYLE_ABORTED = ACTIVE.error


# A guard so a new role is given to every theme: each Theme field must be set.
# (Catches a forgotten field in a builder at import, not in a view at runtime.)
def _check_complete() -> None:
    for theme in THEMES.values():
        for field in fields(Theme):
            if not getattr(theme, field.name):
                raise ValueError(f"theme missing {field.name}")


_check_complete()
