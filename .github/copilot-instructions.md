# puzpy - Python Crossword Puzzle Parser

puzpy is a Python library for parsing .puz crossword puzzle files. It provides a single module (`puz.py`) that can read, write, and manipulate crossword puzzle files in the standard .puz format used by Across Lite and other crossword applications.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Environment Setup
- Change to repository root: `cd /home/runner/work/puzpy/puzpy`
- Python 3.8+ is required (currently tested on 3.10-3.13)
- Install testing dependencies: `pip install pytest pytest-readme flake8 coverage tox`
- Install package in development mode: `pip install -e .` (takes ~3 seconds)

### Running Tests
- **Main test suite**: `pytest tests.py -v` - Takes ~0.14s, runs 40 tests. NEVER CANCEL.
- **README tests**: `pytest test_readme.py -v` - Takes ~0.01s, runs 1 test.
- **All tests**: `pytest -v` - Takes ~0.35s, runs 41 tests. NEVER CANCEL.
- **Direct execution**: `python tests.py` - Alternative way to run all tests.
- **Coverage**: `coverage run tests.py && coverage html` - Takes ~2s total, generates htmlcov/index.html.

### Code Quality
- **Linting**: `flake8 . --count --show-source --statistics` - Takes ~0.25s. Currently has 14 style issues (expected).
- **Tox environments**: `tox -e lint` for linting, `tox -e coverage` for coverage (may fail due to network timeouts).

### Manual Validation
Always test these scenarios after making changes to ensure functionality:

```python
import puz

# Test 1: Load and read a standard puzzle
p = puz.read('testfiles/washpost.puz')
print(f"Title: {p.title}")
print(f"Size: {p.width}x{p.height}")

# Test 2: Parse clues and solutions
numbering = p.clue_numbering()
solution = puz.Grid(p.solution, p.width, p.height)
print(f"First across: {numbering.across[0]['clue']} = {solution.get_string_for_clue(numbering.across[0])}")

# Test 3: Load text format
p2 = puz.read_text('testfiles/text_format_v1.txt')
print(f"Text format title: {p2.title}")

# Test 4: Check locked puzzle detection
p3 = puz.read('testfiles/nyt_locked.puz')
print(f"Is locked: {p3.is_solution_locked()}")
```

**Expected outputs:**
- Title: "December 6, 2005 - "Split Pea Soup""
- Size: 15x15
- First across: "Mary's pet = LAMB"
- Text format title: "Politics: Who, what, where and why"
- Is locked: True

## Build and Installation

### No Build Required
- **This is a pure Python library with no build step.**
- The main module `puz.py` works directly without compilation.
- For development: work directly with the source file.
- For testing: run tests directly with pytest or python.

### Installation for Distribution
- `pip install -e .` - Install in development mode (recommended for development)
- `pip install .` - Install normally
- Package can be imported as `import puz` after installation

### Distribution Files
- Main library: `puz.py` (31KB, single file)
- Test files: `tests.py` (40 test functions), `test_readme.py` (1 test)
- Test data: `testfiles/` directory with 15 sample puzzle files
- Configuration: `pyproject.toml`, `tox.ini`, `pytest.ini`, `.flake8`

## Repository Structure

```
puzpy/
├── puz.py                    # Main library (31KB)
├── tests.py                  # Test suite (40 tests)
├── test_readme.py           # README example tests (1 test)
├── testfiles/               # Sample puzzle files (15 files)
│   ├── washpost.puz         # Standard test puzzle
│   ├── text_format_v1.txt   # Text format example
│   ├── nyt_locked.puz       # Locked puzzle example
│   └── ...                  # Other test puzzles
├── pyproject.toml           # Package configuration
├── tox.ini                  # Tox test configuration
├── pytest.ini              # Pytest configuration
├── .flake8                  # Flake8 linting configuration
└── .github/workflows/       # CI configuration
    └── python-package.yml   # Tests on Python 3.10-3.13
```

## Common Tasks

### Testing After Changes
1. `pytest tests.py -v` - Verify core functionality
2. `python -c "import puz; p=puz.read('testfiles/washpost.puz'); print(p.title)"` - Quick smoke test
3. `flake8 . --count --show-source --statistics` - Check code style
4. Run the manual validation code above

### Working with Puzzle Files
- **Load puzzle**: `p = puz.read('path/to/puzzle.puz')`
- **Load text format**: `p = puz.read_text('path/to/puzzle.txt')`
- **Access basic info**: `p.title`, `p.author`, `p.width`, `p.height`
- **Get clues**: `numbering = p.clue_numbering()` then `numbering.across` and `numbering.down`
- **Get solutions**: `solution = puz.Grid(p.solution, p.width, p.height)`
- **Save puzzle**: `p.save('output.puz')`

### Error Handling
- **Missing files**: Raises `FileNotFoundError`
- **Invalid format**: Raises `puz.PuzzleFormatError`
- **Checksum errors**: Raises `puz.PuzzleFormatError` with specific message

## CI and Validation

### GitHub Actions
- Workflow: `.github/workflows/python-package.yml`
- Tests on Python 3.10, 3.11, 3.12, 3.13
- Runs: `tox -e py` (which runs pytest)
- Triggered on: push to master, pull requests to master

### Pre-commit Checks
Before committing changes, always run:
1. `pytest -v` - Ensure all tests pass (~0.35s)
2. `flake8 . --count --show-source --statistics` - Check for style issues (~0.25s)
3. Manual validation scenarios above

### Known Limitations
- Tox may fail due to network timeouts when installing dependencies
- Some flake8 style issues exist in the codebase (14 issues currently)
- test_readme.py is auto-generated and excluded from flake8 checking
- No unittest framework tests - everything uses pytest

## Timeouts and Performance
- **All tests complete in under 1 second** - very fast test suite
- **No long-running builds** - pure Python, no compilation needed
- **Network operations**: Only during `pip install` and `tox` dependency installation
- **Set timeouts to 60+ seconds minimum** for any pip/tox operations due to potential network issues

## Library Usage Examples

The library supports reading puzzle files, manipulating puzzle data, converting between formats, and handling locked/scrambled puzzles. Test files in `testfiles/` provide examples of various puzzle formats and edge cases that the library handles correctly.