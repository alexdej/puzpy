# puz.py: Python parser for .puz files
[![PyPI - Version](https://img.shields.io/pypi/v/puzpy)](https://pypi.org/project/puzpy/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/puzpy)](https://pypi.org/project/puzpy/)
[![PyPI - License](https://img.shields.io/pypi/l/puzpy)](https://opensource.org/licenses/MIT)
[![GitHub branch check runs](https://img.shields.io/github/check-runs/alexdej/puzpy/master)](https://github.com/alexdej/puzpy/actions/workflows/build.yml)
[![Coverage](https://img.shields.io/badge/dynamic/json?url=https://alexdej.github.io/puzpy/coverage/coverage.json&query=$.totals.percent_covered_display&suffix=%25&label=coverage)](https://alexdej.github.io/puzpy/coverage/)


Python library to read and write crossword puzzle files in Across Lite `.puz` and `.txt` formats.

## Installing

### From pypi (recommended)
```bash skip
pip install puzpy
```

### From source (for development)
```bash skip
pip install .[dev]
```

## Example Usage

```python
import puz

#
# Load a puzzle file:
#
p = puz.read('testfiles/washpost.puz')

#
# Print all clues and their answers
#
clues = p.clue_numbering()

print('Across')
for clue in clues.across:
    print(clue.number, clue.text, '-', clue.solution)

print('Down')
for clue in clues.down:
    print(clue.number, clue.text, '-', clue.solution)

#
# Print the puzzle grid
#
for row in p.grid():
    print(' '.join(row))

#
# Unlock a puzzle that has a locked solution
#
p.unlock_solution(7844)

# Now print the unscrambed solution grid:
for row in p.solution_grid():
    print(' '.join(row))

#
# Save a puzzle with modifications:
#
p.fill = 'LAMB' + p.fill[:4]
p.save('example.puz')

#
# New! Convert from Across Lite text format to .puz:
#
p2 = puz.read_text('testfiles/text_format_v1.txt')
p2.save('example2.puz')
```
## Notes

The parser is as strict as Across Lite, enforcing internal checksums and
magic strings. The parser is designed to round-trip all data in the
file, even fields whose utility is unknown. This makes testing easier.
It is resilient to garbage at the beginning and end of the file (for
example some publishers put the filename on the first line and some
files have a rn at the end).

In addition to the handful of tests checked in here, the library has
been tested on over 9700 crossword puzzles in .puz format drawn from the
archives of several publications including The New York Times, The
Washington Post, The Onion, and, the Wall Street Journal. As of writing,
it can round-trip 100% of them with full fidelity.

## Running tests
[![Build and run tests](https://github.com/alexdej/puzpy/actions/workflows/build.yml/badge.svg)](https://github.com/alexdej/puzpy/actions/workflows/build.yml)

### Unit tests
```bash skip
pytest -v
```

### lint
```bash skip
flake8 . --show-source --statistics
```

## Viewer

This project comes with a bundled puz file viewer. Examples: [15x15](https://alexdej.github.io/puzpy/viewer/washpost.html), [21x21](https://alexdej.github.io/puzpy/viewer/wsj110624.html)
```skip
$ python -m puz_viewer --help
usage: puz_viewer.py [-h] [-o OUTFILE] [--outdir OUTDIR] [-f {auto,puz,txt}] [--index] [puzzles ...]

Generate an HTML viewer for a crossword puzzle or puzzles

positional arguments:
  puzzles               Paths to .puz or .txt files (default: stdin)

options:
  -h, --help            show this help message and exit
  -o, --outfile OUTFILE
                        Output HTML filename (default: stdout, or auto-generated from input filename in batch mode)
  --outdir OUTDIR       Output directory for HTML files (default: .)
  -f, --format {auto,puz,txt}
                        Input format (default: auto-detect)
  --index               Generate index.html in output directory (batch mode)
```

## Python version support
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/puzpy)

Python >=3.9 required since `0.3.1`. For older python versions including 2.x use `puzpy==0.2.6`

## Resources

- [AcrossLite .puz file format](FileFormat.md) (archived from http://code.google.com/p/puz/wiki/FileFormat)
- [Across text format](AcrossTextFormat.md) (archived from https://www.litsoft.com/across/docs/AcrossTextFormat.pdf)

## License

MIT License.
