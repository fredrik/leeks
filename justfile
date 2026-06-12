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

# Land a feature branch: semi-linear merge marker, then clean up the branch.
# Without an argument, fzf picks the branch. --ff and --squash change the mode.
land *args:
    ./scripts/land {{args}}

# Materialise the fixture corpus as tagged audio to play with.
materialise dest="/tmp/leeks-scratch":
    uv run python tests/fixtures/materialise.py {{dest}}
    echo
    echo 'try: LEEKS_ROOT={{dest}}-library leek add {{dest}}/Salt-Meridian'

clean:
    find . -name .venv -prune -o -type d -name __pycache__ -prune -exec rm -rf {} +
    rm -rf .pytest_cache .ruff_cache
