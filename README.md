# puz.py: Python parser for .puz files

Python library to read and write crossword puzzle files in Across Lite `.puz` and/or `.txt` formats.

## Example Usage

```python
import puz

# Load a puzzle file:
p = puz.read('testfiles/washpost.puz')

# Print clues with answers:
numbering = p.clue_numbering()
solution = puz.Grid(p.solution, p.width, p.height)

print('Across')
for clue in numbering.across:
    answer = solution.get_string_for_clue(clue)
    print(clue['num'], clue['clue'], '-', answer)

print('Down')
for clue in numbering.down:
    answer = solution.get_string_for_clue(clue)
    print(clue['num'], clue['clue'], '-', answer)

# Print the grid:
grid = puz.Grid(p.fill, p.width, p.height)
for row in range(p.height):
    print(' '.join(grid.get_row(row)))

# Unlock a scrambled solution:
p.unlock_solution(7844)

# Print the unscrambed solution grid:
solution = puz.Grid(p.solution, p.width, p.height)
for row in range(p.height):
    print(' '.join(solution.get_row(row)))

# Save a puzzle with modifications:
p.fill = 'LAMB' + p.fill[4:]
p.save('example.puz')

# New! Convert from Across Lite text format to .puz:
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

To run the full suite of tests:
```tox```

To run tests using the currently installed version:
```pytest```

To run a subset of tests on python 2.7:
```python2 -m unittest tests```

## Python version support

All currently supported python3 versions are supported. Python 2.7 was supported, 
and may still work, though ongoing support is not guaranteed. 

## Resources

- [`.puz` file format](http://code.google.com/p/puz/wiki/FileFormat)
- [`.txt` file format](https://www.litsoft.com/across/docs/AcrossTextFormat.pdf)
- [Archive of NYT daily puzzles 1993 - August 2021](https://archive.org/details/nyt-puz)
- [`.puz` to `.pdf` file converter](https://www.crosswordnexus.com/apps/puz-to-pdf/)

## License

MIT License.
