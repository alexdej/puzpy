puz.py: python crossword puzzle library (.puz file parser)
=============
Implementation of .puz crossword puzzle file parser based on .puz file format documentation here: http://code.google.com/p/puz/wiki/FileFormat

The parser is as strict as Across Lite, enforcing internal checksums and magic strings. The parser is designed to round-trip all data in the file, even fields whose utility is unknown. This makes testing easier. It is resilient to garbage at the beginning and end of the file (for example some publishers put the filename on the first line and some files have a \r\n at the end).

In addition to the handful of tests checked in here, the library has been tested on over 9700 crossword puzzles in .puz format drawn from the archives of several publications including The New York Times, The Washington Post, The Onion, and, the Wall Street Journal. As of writing, it can round-trip 100% of them with full fidelity.

MIT License.

