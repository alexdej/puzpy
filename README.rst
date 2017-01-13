puz.py: python crossword puzzle library (.puz file parser)
=============
Implementation of .puz crossword puzzle file parser based on .puz file format documentation here: http://code.google.com/p/puz/wiki/FileFormat

Examples
--------
Load a puzzle file::

  import puz
  p = puz.read('testfiles/washpost.puz')

Print clues with answers::

  numbering = p.clue_numbering()

  print 'Across'
  for clue in numbering.across:
      answer = ''.join(
          p.solution[clue['cell'] + i]
          for i in range(clue['len']))
      print clue['num'], clue['clue'], '-', answer

  print 'Down'
  for clue in numbering.down:
      answer = ''.join(
          p.solution[clue['cell'] + i * numbering.width]
          for i in range(clue['len']))
      print clue['num'], clue['clue'], '-', answer

Print the grid::

  for row in range(p.height):
      cell = row * p.width
      # Substitute p.solution for p.fill to print the answers
      print ' '.join(p.fill[cell:cell + p.width])

Unlock a scrambled solution::

    p.unlock_solution(7844)
    # p.solution is unscambled

Save a puzzle with modifications::

    p.fill = 'LAMB' + p.fill[4:]
    p.save('mine.puz')

Notes
-----
The parser is as strict as Across Lite, enforcing internal checksums and magic strings. The parser is designed to round-trip all data in the file, even fields whose utility is unknown. This makes testing easier. It is resilient to garbage at the beginning and end of the file (for example some publishers put the filename on the first line and some files have a \r\n at the end).

In addition to the handful of tests checked in here, the library has been tested on over 9700 crossword puzzles in .puz format drawn from the archives of several publications including The New York Times, The Washington Post, The Onion, and, the Wall Street Journal. As of writing, it can round-trip 100% of them with full fidelity.

Running tests
-------------
`python tests.py`

License
------
MIT License.
