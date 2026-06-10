# Quality gates. `just` alone runs check.

check:
    uv run ruff format --check .
    uv run ruff check .
    uv run mdformat --check .
    uv run ty check
    uv run pytest

fix:
    uv run ruff format .
    uv run ruff check --fix .
    uv run mdformat .
    uv run ty check
    uv run pytest
