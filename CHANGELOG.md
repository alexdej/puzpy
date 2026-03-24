# Changelog

## 0.6.0 (Mar 24, 2026)
Improved API for Clues and Grid

ClueEntry now has named properties for cleaner, more discoverable access:

clues = p.clue_numbering()
for clue in clues.across:
    print(f'{clue.number}. {clue.text} - {clue.solution}')

New convenience methods on Puzzle:
- p.grid() / p.solution_grid() — return a Grid directly
- Grid is now iterable (rows by default), with .rows() and .cols() iterators

Dict-style access (clue['num'], clue['clue']) continues to work for backwards compatibility.

Better Debugging with __repr__

All core objects (Puzzle, Grid, ClueNumbering, Rebus, Markup, Timer, PuzzleBuffer) now have informative __repr__ methods.

## 0.5.0 (Mar 20, 2026)

- LTIM (timer) support, with new Timer class that exposes timer status and elapsed_seconds
- RUSR (rebus fill) support, so rebus user fill from Across Lite can be read/written.
- check_rebus_answers() to validate rebus fill entries against their solutions
- check_answers(strict=False) enables validation of a partially filled grid.
- Across Lite Text Version 2 support: REBUS section and MARK flags (circled cells)
- helper methods on Rebus and Markup to make it easier to create rebus table and markup
- PEP 484-style type annotation throughout the project.

## 0.4.2 (Mar 19, 2026)

- Increment version number

## 0.4.1 (Mar 19, 2026)

- Added requires-python = ">=3.9" and updated list of supported python versions. Python 3.8 was broken in 0.3.1 with upgrade to setuptools >= 77.0.3
- Fixed issue #53 Rebus.save() injects spurious RUSR extension on save
- Fixed issue #54 Leading space stripped from rebus solution keys on save

## 0.4.0 (Mar 18, 2026)

Added requires-python = ">=3.8" and updated list of supported python versions.

Last release that supported python 2.7 was 0.2.6. python2 compatibility was broken in 0.3.1 with upgrade to setuptools >= 77.0.3. This change makes it official.

## 0.3.2 (Oct 23, 2025)

- Increment version number

## 0.3.1  (Oct 23, 2025)

Hotfix for problem with build packaging in 0.3.0 -- missing puz.py module.

## 0.3.0 (Oct 23, 2025)

- new Grid helper class to simplify access to clues
- support for reading and writing files in AcrossLite text format
- bug fix (courtesy @afontenot) to allow serialized dicts to have ':' in values

## 0.2.6 (Jun 12, 2024)

- Add NotProvided value to SolutionState enum for puzzles without a
  solution
- typo in Markup.is_markup_square
- utf-8 support for v2 files
- various fixes for diagramless

## 0.2.5 (Jun 7, 2019)

- added support for puz file version 1.4

## 0.2.4 (March 15, 2019)

- minor bug fixes

## 0.2.3 (October 24, 2016)

- Incremented version number as needed for for PyPI.

## 0.2.2 (October 24, 2016)

- Added support for Python 2.6

## 0.2.1 (December 19, 2014)

- Added version string to puz module for version detection.

## 0.2 (December 19, 2014)

- Added support for Python 3.2+.
- Fixed issue where tests were not added properly to TestSuite.

## 0.1 (February 16, 2014)

- Initial release.
