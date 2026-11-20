# Agent instructions for puzpy

puzpy is a Python library for reading and writing crossword puzzle files in the
Across Lite `.puz` (binary) and `.txt` (text) formats. The library is a single
module, `puz.py`, with no runtime dependencies.

If anything here disagrees with `pyproject.toml`, `README.md` or
`.github/workflows/build.yml`, those files are right and this one is stale.

## Layout

- `puz.py`: the library. Everything public lives here.
- `tests.py`: the pytest suite.
- `testfiles/`: sample `.puz` and `.txt` puzzles used by the tests.
- `README.md`: user docs. Its Python code blocks are executed as tests.
- `puz_viewer.py`: script that renders a puzzle as a stand-alone HTML file.
- `viewer_template.html`, `sync_template.py`: source and sync script for the
  HTML template embedded in `puz_viewer.py`.
- `FileFormat.md`, `AcrossTextFormat.md`: archived format references. Read
  these before changing parsing or checksum code.
- `pyproject.toml`: packaging and all tool configuration (pytest, coverage,
  ruff, pyright).
- `.github/workflows/build.yml`: CI. `.github/workflows/publish.yml`: PyPI
  release on a version tag.

## Setup

Run everything from the repository root. The project uses
[uv](https://docs.astral.sh/uv/):

```bash
uv sync --extra dev
```

## Checks

CI runs these three commands, and all three must pass before a change is done:

```bash
uv run pytest
```

```bash
uv run ruff check
```

```bash
uv run pyright
```

Notes:

- `uv run pytest` collects `tests.py` and the code blocks in `README.md`
  (through pytest-codeblocks, enabled by `addopts = "--codeblocks"` in
  `pyproject.toml`). If you change the public API, the README examples have to
  keep working. README blocks marked `skip` are not executed.
- To run a subset: `uv run pytest tests.py -k <expression>`.
- For coverage: `uv run pytest --cov`.
- `tests.py` has no `__main__` block. Running `python tests.py` does nothing;
  use pytest.
- The README test writes `example.puz` in the repository root. It is ignored
  by git (`example*.puz` in `.gitignore`).

## Constraints

- Code must run on every Python version in the CI matrix in
  `.github/workflows/build.yml`. The minimum is `requires-python` in
  `pyproject.toml`; ruff (`target-version`) and pyright (`pythonVersion`) are
  both pinned to that minimum, so newer syntax and stdlib APIs will fail lint
  or type check.
- `puz.py` stays a single file with no third-party imports.
- Ruff's line length and rule set are in `[tool.ruff]` in `pyproject.toml`.
- A bug fix or behavior change needs a test in `tests.py` that fails without
  the change. If it needs a new puzzle file, add it to `testfiles/`.
- User-visible changes get an entry in `CHANGELOG.md`.

## Smoke test

A quick end-to-end check from the repository root:

```bash
uv run python -c "import puz; p = puz.read('testfiles/washpost.puz'); c = p.clue_numbering().across[0]; print(p.width, p.height, c.number, c.text, c.solution)"
```

Expected output: `15 15 1 Mary's pet LAMB`

## Viewer

`puz_viewer.py` contains a copy of `viewer_template.html` as a string. Edit the
HTML file, not the string, then sync:

```bash
uv run python sync_template.py --write
```

Without `--write` the script is a dry run that shows the diff. To render a
puzzle:

```bash
uv run python puz_viewer.py testfiles/washpost.puz -o washpost.html
```

## Contributing

If a `CONTRIBUTING.md` exists at the repository root, read it before opening an
issue or pull request, and follow it over anything in this file. Do not open a
pull request unless the person you are working for asked for one.
