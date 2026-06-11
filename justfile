# Quality gates. `just` alone runs check.

set quiet

check:
    uv run --quiet ruff format --check --quiet .
    uv run --quiet ruff check --quiet .
    uv run --quiet mdformat --check .
    uv run --quiet ty check --quiet
    uv run --quiet pytest --quiet

fix:
    uv run --quiet ruff format --quiet .
    uv run --quiet ruff check --fix --quiet .
    uv run --quiet mdformat .
    uv run --quiet ty check --quiet
    uv run --quiet pytest --quiet
