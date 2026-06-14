"""Theme selection: LEEKS_THEME picks a theme; the views read roles (ADR 0028)."""

import os
import subprocess
from dataclasses import fields

from leeks import theme

# Catppuccin Mocha mauve #cba6f7, Latte mauve #8839ef, Gruvbox purple #d3869b,
# each as the truecolor escape rich emits for the artist/usage role.
MOCHA_ACCENT = "38;2;203;166;247"
LATTE_ACCENT = "38;2;136;57;239"
GRUVBOX_ACCENT = "38;2;211;134;155"


def test_select_names_a_theme():
    assert theme._select("latte") is theme.THEMES["latte"]
    assert theme._select("gruvbox") is theme.THEMES["gruvbox"]


def test_select_folds_case_and_trims():
    # LEEKS_THEME=Latte or " latte " both land on latte (a forgiving env var).
    assert theme._select("  LATTE ") is theme.THEMES["latte"]


def test_unknown_theme_falls_back_to_default():
    # A misremembered name leaves leek usable in the default dress, never errors.
    assert theme._select("nonsense") is theme.THEMES[theme.DEFAULT]
    assert theme._select(None) is theme.THEMES[theme.DEFAULT]
    assert theme.DEFAULT == "mocha"


def test_every_theme_binds_every_role():
    # The decoupling contract (ADR 0028): a role is a slot every theme fills, so
    # no view can hit an empty style. The import-time guard enforces it too.
    for name, t in theme.THEMES.items():
        for field in fields(theme.Theme):
            value = getattr(t, field.name)
            assert value, f"{name} leaves {field.name} unset"
        assert len(t.rainbow) == 6, f"{name} rainbow is not the spectral six"


def test_roles_carry_no_loose_colour_names():
    # The honesty check (ADR 0028): a style is bold/italic plus a hex, never a
    # bare colour word like "mauve" — colour names stay private to the builders.
    for t in theme.THEMES.values():
        for field in fields(theme.Theme):
            if field.name == "rainbow":
                continue
            for token in getattr(t, field.name).split():
                assert token in ("bold", "italic", "dim") or token.startswith("#")


def _help_under_theme(name: str | None) -> str:
    env = {**os.environ, "FORCE_COLOR": "1", "COLORTERM": "truecolor"}
    if name is not None:
        env["LEEKS_THEME"] = name
    else:
        env.pop("LEEKS_THEME", None)
    result = subprocess.run(["leek", "help"], capture_output=True, text=True, env=env)
    assert result.returncode == 0
    return result.stdout


def test_leeks_theme_env_var_recolours_the_help():
    # End to end: the env var actually changes the colour on screen. Latte's
    # accent appears, Mocha's does not — the whole pipeline honoured the choice.
    latte = _help_under_theme("latte")
    assert LATTE_ACCENT in latte
    assert MOCHA_ACCENT not in latte


def test_gruvbox_is_entirely_different():
    gruvbox = _help_under_theme("gruvbox")
    assert GRUVBOX_ACCENT in gruvbox
    assert MOCHA_ACCENT not in gruvbox


def test_no_theme_or_unknown_theme_is_mocha():
    assert MOCHA_ACCENT in _help_under_theme(None)
    assert MOCHA_ACCENT in _help_under_theme("nonsense")
