from __future__ import annotations  # for Python 3.9 and earlier

import functools
import importlib.metadata
import operator
import math
import string
import struct
from enum import Enum, IntEnum
from typing import Any, Iterable, Protocol, TypedDict, cast, runtime_checkable

__version__ = importlib.metadata.version('puzpy')

HEADER_FORMAT = '''<
             H 11s        xH
             Q       4s  2sH
             12s         BBH
             H H '''

HEADER_CKSUM_FORMAT = '<BBH H H '

EXTENSION_HEADER_FORMAT = '< 4s  H H '

MASKSTRING = 'ICHEATED'

ENCODING = 'ISO-8859-1'
ENCODING_UTF8 = 'UTF-8'
ENCODING_ERRORS = 'strict'  # raises an exception for bad chars; change to 'replace' for laxer handling

ACROSSDOWN = b'ACROSS&DOWN'

BLACKSQUARE = '.'
BLACKSQUARE2 = ':'  # used for diagramless puzzles
BLANKSQUARE = '-'


class PuzzleType(IntEnum):
    Normal = 0x0001
    Diagramless = 0x0401


# the following diverges from the documentation
# but works for the files I've tested
class SolutionState(IntEnum):
    # solution is available in plaintext
    Unlocked = 0x0000
    # solution is not present in the file
    NotProvided = 0x0002
    # solution is locked (scrambled) with a key
    Locked = 0x0004


class GridMarkup(IntEnum):
    # ordinary grid cell
    Default = 0x00
    # marked incorrect at some point
    PreviouslyIncorrect = 0x10
    # currently showing incorrect
    Incorrect = 0x20
    # user got a hint
    Revealed = 0x40
    # circled
    Circled = 0x80


# refer to Extensions as Extensions.Rebus, Extensions.Markup
class Extensions(bytes, Enum):
    # grid of rebus indices: 0 for non-rebus;
    # i+1 for key i into RebusSolutions map
    # should be same size as the grid
    Rebus = b'GRBS',

    # map of rebus solution entries eg 0:HEART;1:DIAMOND;17:CLUB;23:SPADE;
    RebusSolutions = b'RTBL',

    # user's rebus entries; binary grid format: one null-terminated string per cell (in grid order).
    # empty cells are a single null byte; filled rebus cells are the fill string followed by a null byte.
    RebusFill = b'RUSR',

    # timer state: 'a,b' where a is the number of seconds elapsed and
    # b is a boolean (0,1) for whether the timer is running
    Timer = b'LTIM',

    # grid cell markup: previously incorrect: 0x10;
    # currently incorrect: 0x20,
    # hinted: 0x40,
    # circled: 0x80
    Markup = b'GEXT'


class ClueEntry(TypedDict):
    num: int
    clue: str | None  # None until filled in by DefaultClueNumbering.__init__
    clue_index: int
    cell: int
    row: int
    col: int
    len: int
    dir: str


def read(filename: str) -> 'Puzzle':
    """
    Read a .puz file and return the Puzzle object.
    raises PuzzleFormatError if there's any problem with the file format.
    """
    with open(filename, 'rb') as f:
        return load(f.read())


def read_text(filename: str) -> 'Puzzle':
    """
    Read an Across Lite .txt text format file and return the Puzzle object.
    raises PuzzleFormatError if there's any problem with the file format.
    """
    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
        return load_text(f.read())


def load(data: bytes) -> 'Puzzle':
    """
    Read .puz file data and return the Puzzle object.
    raises PuzzleFormatError if there's any problem with the file format.
    """
    puz = Puzzle()
    puz.load(data)
    return puz


def load_text(text: str) -> 'Puzzle':
    """
    Parse Across Lite Text format from a string and return a Puzzle object.
    raises PuzzleFormatError if there's any problem with the format.
    """
    return from_text_format(text)


class PuzzleFormatError(Exception):
    """
    Indicates a format error in the .puz file. May be thrown due to
    invalid headers, invalid checksum validation, or other format issues.
    """
    def __init__(self, message: str = '') -> None:
        self.message = message


class Puzzle:
    """Represents a puzzle
    """
    def __init__(self, version: str | bytes = '1.3') -> None:
        """Initializes a blank puzzle
        """
        self.preamble = b''
        self.postscript: bytes | str = b''
        self.title = ''
        self.author = ''
        self.copyright = ''
        self.width = 0
        self.height = 0
        self.set_version(version)
        self.encoding = ENCODING
        # these are bytes that might be unused
        self.unk1 = b'\0' * 2
        self.unk2 = b'\0' * 12
        self.scrambled_cksum = 0
        self.fill = ''
        self.solution = ''
        self.clues: list[str] = []
        self.notes = ''
        self.extensions: dict[bytes, bytes] = {}
        # the folowing is so that we can round-trip values in order:
        self._extensions_order: list[bytes] = []
        self.puzzletype = PuzzleType.Normal
        self.solution_state = SolutionState.Unlocked
        self.helpers: dict[str, 'PuzzleHelper'] = {}  # add-ons like Rebus and Markup

    def load(self, data: bytes) -> None:
        s = PuzzleBuffer(data)

        # advance to start - files may contain some data before the
        # start of the puzzle use the ACROSS&DOWN magic string as a waypoint
        # save the preamble for round-tripping
        if not s.seek_to(ACROSSDOWN, -2):
            raise PuzzleFormatError("Data does not appear to represent a "
                                    "puzzle. Are you sure you didn't intend "
                                    "to use read?")

        # save whatever we just jumped over so that we can round-trip it on save.
        self.preamble = bytes(s.data[:s.pos])

        puzzle_data = s.unpack(HEADER_FORMAT)
        cksum_gbl = puzzle_data[0]
        # acrossDown = puzzle_data[1]
        cksum_hdr = puzzle_data[2]
        cksum_magic = puzzle_data[3]
        self.fileversion = puzzle_data[4]
        # since we don't know the role of these bytes, just round-trip them
        self.unk1 = puzzle_data[5]
        self.scrambled_cksum = puzzle_data[6]
        self.unk2 = puzzle_data[7]
        self.width = puzzle_data[8]
        self.height = puzzle_data[9]
        numclues = puzzle_data[10]
        self.puzzletype = puzzle_data[11]
        self.solution_state = puzzle_data[12]

        self.version = self.fileversion[:3]
        # Once we have fileversion we can guess the encoding
        self.encoding = ENCODING if self.version_tuple()[0] < 2 else ENCODING_UTF8
        s.encoding = self.encoding

        self.solution = s.read(self.width * self.height).decode(self.encoding)
        self.fill = s.read(self.width * self.height).decode(self.encoding)

        self.title = s.read_string()
        self.author = s.read_string()
        self.copyright = s.read_string()

        self.clues = [s.read_string() for i in range(0, numclues)]
        self.notes = s.read_string()

        ext_cksum = {}
        while s.can_unpack(EXTENSION_HEADER_FORMAT):
            code, length, cksum = s.unpack(EXTENSION_HEADER_FORMAT)
            ext_cksum[code] = cksum
            # extension data is represented as a null-terminated string,
            # but since the data can contain nulls we can't use read_string
            self.extensions[code] = s.read(length)
            s.read(1)  # extensions have a trailing byte
            # save the codes in order for round-tripping
            self._extensions_order.append(code)

        # sometimes there's some extra garbage at
        # the end of the file, usually \r\n
        if s.can_read():
            self.postscript = s.read_to_end()

        if cksum_gbl != self.global_cksum():
            raise PuzzleFormatError('global checksum does not match')
        if cksum_hdr != self.header_cksum():
            raise PuzzleFormatError('header checksum does not match')
        if cksum_magic != self.magic_cksum():
            raise PuzzleFormatError('magic checksum does not match')
        for code, cksum_ext in ext_cksum.items():
            if cksum_ext != data_cksum(self.extensions[code]):
                raise PuzzleFormatError(
                    'extension %s checksum does not match' % code
                )

    def save(self, filename: str) -> None:
        puzzle_bytes = self.tobytes()
        with open(filename, 'wb') as f:
            f.write(puzzle_bytes)

    def tobytes(self) -> bytes:
        s = PuzzleBuffer(encoding=self.encoding)
        # commit any changes from helpers
        for h in self.helpers.values():
            if isinstance(h, PuzzleHelper):
                h.save()

        # include any preamble text we might have found on read
        s.write(self.preamble)

        s.pack(HEADER_FORMAT,
               self.global_cksum(), ACROSSDOWN,
               self.header_cksum(), self.magic_cksum(),
               self.fileversion, self.unk1, self.scrambled_cksum,
               self.unk2, self.width, self.height,
               len(self.clues), self.puzzletype, self.solution_state)

        s.write(self.encode(self.solution))
        s.write(self.encode(self.fill))

        s.write_string(self.title)
        s.write_string(self.author)
        s.write_string(self.copyright)

        for clue in self.clues:
            s.write_string(clue)

        s.write_string(self.notes)

        # do a bit of extra work here to ensure extensions round-trip in the
        # order they were read. this makes verification easier. But allow
        # for the possibility that extensions were added or removed from
        # self.extensions
        ext = dict(self.extensions)
        for code in self._extensions_order:
            data = ext.pop(code, None)
            if data:
                s.pack(EXTENSION_HEADER_FORMAT, code,
                       len(data), data_cksum(data))
                s.write(data + b'\0')

        for code, data in ext.items():
            s.pack(EXTENSION_HEADER_FORMAT, code, len(data), data_cksum(data))
            s.write(data + b'\0')

        # postscript is initialized, read, and stored as bytes. In case it is
        # overwritten as a string, this try/except converts it back.
        postscript_bytes = self.postscript.encode(self.encoding, ENCODING_ERRORS) \
            if isinstance(self.postscript, str) else self.postscript
        s.write(postscript_bytes)

        return s.tobytes()

    def encode(self, s: str) -> bytes:
        return s.encode(self.encoding, ENCODING_ERRORS)

    def encode_zstring(self, s: str) -> bytes:
        return self.encode(s) + b'\0'

    def version_tuple(self) -> tuple[int, ...]:
        return tuple(map(int, self.version.split(b'.')))

    def set_version(self, version: str | bytes) -> None:
        self.version = version.encode('utf-8') if isinstance(version, str) else bytes(version)
        self.fileversion = self.version + b'\0'

    def has_rebus(self) -> bool:
        return self.rebus().has_rebus()

    def rebus(self) -> 'Rebus':
        if 'rebus' not in self.helpers:
            self.helpers['rebus'] = Rebus(self)
        return cast('Rebus', self.helpers['rebus'])

    def has_timer(self) -> bool:
        return Extensions.Timer in self.extensions or 'timer' in self.helpers

    def remove_timer(self) -> None:
        self.extensions.pop(Extensions.Timer, None)
        self.helpers.pop('timer', None)

    def timer(self) -> 'Timer':
        if 'timer' not in self.helpers:
            self.helpers['timer'] = Timer(self)
        return cast('Timer', self.helpers['timer'])

    def has_markup(self) -> bool:
        return self.markup().has_markup()

    def markup(self) -> 'Markup':
        if 'markup' not in self.helpers:
            self.helpers['markup'] = Markup(self)
        return cast('Markup', self.helpers['markup'])

    def clue_numbering(self) -> 'DefaultClueNumbering':
        if 'clues' not in self.helpers:
            self.helpers['clues'] = DefaultClueNumbering(self.fill, self.clues, self.width, self.height)
        return cast('DefaultClueNumbering', self.helpers['clues'])

    def blacksquare(self) -> str:
        return BLACKSQUARE2 if self.puzzletype == PuzzleType.Diagramless else BLACKSQUARE

    def is_solution_locked(self) -> bool:
        return bool(self.solution_state == SolutionState.Locked)

    def unlock_solution(self, key: int) -> bool:
        if self.is_solution_locked():
            unscrambled = unscramble_solution(self.solution, self.width, self.height, key,
                                              ignore_chars=self.blacksquare())
            if not self.check_answers(unscrambled):
                return False

            # clear the scrambled bit and cksum
            self.solution = unscrambled
            self.scrambled_cksum = 0
            self.solution_state = SolutionState.Unlocked

        return True

    def lock_solution(self, key: int) -> None:
        if not self.is_solution_locked():
            # set the scrambled bit and cksum
            self.scrambled_cksum = scrambled_cksum(self.solution, self.width, self.height,
                                                   ignore_chars=self.blacksquare(), encoding=self.encoding)
            self.solution_state = SolutionState.Locked
            scrambled = scramble_solution(self.solution, self.width, self.height, key,
                                          ignore_chars=self.blacksquare())
            self.solution = scrambled

    def check_answers(self, fill: str) -> bool:
        if self.is_solution_locked():
            scrambled = scrambled_cksum(fill, self.width, self.height,
                                        ignore_chars=self.blacksquare(), encoding=self.encoding)
            return scrambled == self.scrambled_cksum
        else:
            return fill == self.solution

    def header_cksum(self, cksum: int = 0) -> int:
        return data_cksum(struct.pack(HEADER_CKSUM_FORMAT,
                          self.width, self.height, len(self.clues),
                          self.puzzletype, self.solution_state), cksum)

    def text_cksum(self, cksum: int = 0) -> int:
        # for the checksum to work these fields must be added in order with
        # null termination, followed by all non-empty clues without null
        # termination, followed by notes (but only for version >= 1.3)
        if self.title:
            cksum = data_cksum(self.encode_zstring(self.title), cksum)
        if self.author:
            cksum = data_cksum(self.encode_zstring(self.author), cksum)
        if self.copyright:
            cksum = data_cksum(self.encode_zstring(self.copyright), cksum)

        for clue in self.clues:
            if clue:
                cksum = data_cksum(self.encode(clue), cksum)

        # notes included in global cksum starting v1.3 of format
        if self.version_tuple() >= (1, 3) and self.notes:
            cksum = data_cksum(self.encode_zstring(self.notes), cksum)

        return cksum

    def global_cksum(self) -> int:
        cksum = self.header_cksum()
        cksum = data_cksum(self.encode(self.solution), cksum)
        cksum = data_cksum(self.encode(self.fill), cksum)
        cksum = self.text_cksum(cksum)
        # extensions do not seem to be included in global cksum
        return cksum

    def magic_cksum(self) -> int:
        cksums = [
            self.header_cksum(),
            data_cksum(self.encode(self.solution)),
            data_cksum(self.encode(self.fill)),
            self.text_cksum()
        ]

        cksum_magic = 0
        for (i, cksum) in enumerate(reversed(cksums)):
            cksum_magic <<= 8
            cksum_magic |= (
                ord(MASKSTRING[len(cksums) - i - 1]) ^ (cksum & 0x00ff)
            )
            cksum_magic |= (
                (ord(MASKSTRING[len(cksums) - i - 1 + 4]) ^ (cksum >> 8)) << 32
            )

        return cksum_magic


class PuzzleBuffer:
    """PuzzleBuffer class
    wraps a bytes object and provides .puz-specific methods for
    reading and writing data
    """
    def __init__(self, data: bytes | None = None, encoding: str = ENCODING):
        self.data = bytearray(data) if data else bytearray()
        self.encoding = encoding
        self.pos = 0

    def can_read(self, n_bytes: int = 1) -> bool:
        return self.pos + n_bytes <= len(self.data)

    def length(self) -> int:
        return len(self.data)

    def read(self, n_bytes: int) -> bytes:
        start = self.pos
        self.pos += n_bytes
        return bytes(self.data[start:self.pos])

    def read_to_end(self) -> bytes:
        start = self.pos
        self.pos = self.length()
        return bytes(self.data[start:self.pos])

    def read_string(self) -> str:
        return self.read_until(b'\0')

    def read_until(self, c: bytes) -> str:
        start = self.pos
        self.seek_to(c, 1)  # read past
        return str(self.data[start:self.pos-1], self.encoding)

    def seek_to(self, s: bytes, offset: int = 0) -> bool:
        try:
            self.pos = self.data.index(s, self.pos) + offset
            return True
        except ValueError:
            # s not found, advance to end
            self.pos = self.length()
            return False

    def write(self, s: bytes) -> None:
        self.data.extend(s)

    def write_string(self, s: str | None) -> None:
        s = s or ''
        self.data.extend(s.encode(self.encoding, ENCODING_ERRORS) + b'\0')

    def pack(self, struct_format: str, *values: Any) -> None:
        self.data.extend(struct.pack(struct_format, *values))

    def can_unpack(self, struct_format: str) -> bool:
        return self.can_read(struct.calcsize(struct_format))

    def unpack(self, struct_format: str) -> tuple[Any, ...]:
        start = self.pos
        try:
            res = struct.unpack_from(struct_format, self.data, self.pos)
            self.pos += struct.calcsize(struct_format)
            return res
        except struct.error:
            message = 'could not unpack values at {} for format {}'.format(
                start, struct_format
            )
            raise PuzzleFormatError(message)

    def tobytes(self) -> bytes:
        return bytes(self.data)


# clue numbering helper
def get_grid_numbering(grid: str, width: int, height: int) -> tuple[list[ClueEntry], list[ClueEntry]]:
    # Add numbers to the grid based on positions of black squares
    def col(index: int) -> int:
        return index % width

    def row(index: int) -> int:
        return int(math.floor(index / width))

    def len_across(index: int) -> int:
        c = 0
        for c in range(0, width - col(index)):
            if is_blacksquare(grid[index + c]):
                return c
        return c + 1

    def len_down(index: int) -> int:
        c = 0
        for c in range(0, height - row(index)):
            if is_blacksquare(grid[index + c*width]):
                return c
        return c + 1

    across: list[ClueEntry] = []
    down: list[ClueEntry] = []
    count = 0  # count is the index into the clues list; 0-based and counts across and down together
    num = 1  # num is the clue number that gets printed in the grid
    for i in range(0, len(grid)):  # i is the cell index in row-major order
        if not is_blacksquare(grid[i]):
            lastc = count
            is_across = col(i) == 0 or is_blacksquare(grid[i - 1])
            if is_across and len_across(i) > 1:
                across.append(ClueEntry({
                    'num': num,
                    'clue': None,  # filled in by caller
                    'clue_index': count,
                    'cell': i,
                    'row': row(i),
                    'col': col(i),
                    'len': len_across(i),
                    'dir': 'across',
                }))
                count += 1
            is_down = row(i) == 0 or is_blacksquare(grid[i - width])
            if is_down and len_down(i) > 1:
                down.append(ClueEntry({
                    'num': num,
                    'clue': None,  # filled in by caller
                    'clue_index': count,
                    'cell': i,
                    'row': row(i),
                    'col': col(i),
                    'len': len_down(i),
                    'dir': 'down'
                }))
                count += 1
            if count > lastc:
                num += 1

    return across, down


@runtime_checkable
class PuzzleHelper(Protocol):
    def save(self) -> None:
        ...


class DefaultClueNumbering(PuzzleHelper):
    def __init__(self, grid: str, clues: list[str], width: int, height: int) -> None:
        self.grid = grid
        self.clues = clues
        self.width = width
        self.height = height

        self.across, self.down = get_grid_numbering(grid, width, height)
        for entry in self.across:
            entry['clue'] = clues[entry['clue_index']]
        for entry in self.down:
            entry['clue'] = clues[entry['clue_index']]

    def save(self) -> None:
        pass  # clue numbering is derived from the grid and clues, so no need to save anything back to the puzzle

    # The following methods are no longer in use, but left here in case
    # anyone was using them externally. They may be removed in a future release.
    def col(self, index: int) -> int:
        return index % self.width

    def row(self, index: int) -> int:
        return int(math.floor(index / self.width))

    def len_across(self, index: int) -> int:
        c = 0
        for c in range(0, self.width - self.col(index)):
            if is_blacksquare(self.grid[index + c]):
                return c
        return c + 1

    def len_down(self, index: int) -> int:
        c = 0
        for c in range(0, self.height - self.row(index)):
            if is_blacksquare(self.grid[index + c*self.width]):
                return c
        return c + 1


class Grid:
    def __init__(self, grid: str, width: int, height: int) -> None:
        self.grid = grid
        self.width = width
        self.height = height
        assert len(self.grid) == self.width * self.height

    def get_cell(self, row: int, col: int) -> str:
        return self.grid[self.get_cell_index(row, col)]

    def get_cell_index(self, row: int, col: int) -> int:
        return row * self.width + col

    def get_range(self, row: int, col: int, length: int, dir: str = 'across') -> list[str]:
        if dir == 'across':
            return self.get_range_across(row, col, length)
        elif dir == 'down':
            return self.get_range_down(row, col, length)
        else:
            assert False, "dir not one of 'across' or 'down'"

    def get_range_across(self, row: int, col: int, length: int) -> list[str]:
        return [self.grid[self.get_cell_index(row, col + i)] for i in range(length)]

    def get_range_down(self, row: int, col: int, length: int) -> list[str]:
        return [self.grid[self.get_cell_index(row + i, col)] for i in range(length)]

    def get_range_for_clue(self, clue: ClueEntry) -> list[str]:
        return self.get_range(clue['row'], clue['col'], clue['len'], clue['dir'])

    def get_row(self, row: int) -> list[str]:
        return self.get_range_across(row, 0, self.width)

    def get_column(self, col: int) -> list[str]:
        return self.get_range_down(0, col, self.height)

    def get_string(self, row: int, col: int, length: int, dir: str = 'across') -> str:
        return ''.join(self.get_range(row, col, length, dir))

    def get_string_across(self, row: int, col: int, length: int) -> str:
        return ''.join(self.get_range_across(row, col, length))

    def get_string_down(self, row: int, col: int, length: int) -> str:
        return ''.join(self.get_range_down(row, col, length))

    def get_string_for_clue(self, clue: ClueEntry) -> str:
        return ''.join(self.get_range_for_clue(clue))


class Rebus(PuzzleHelper):
    def __init__(self, puzzle: Puzzle) -> None:
        self.puzzle = puzzle

        N = self.puzzle.width * self.puzzle.height

        self._dirty = False  # track whether there are unsaved changes to the rebus helper that need to be committed
        # to the puzzle before saving

        # the rebus table has the same number of entries as the grid and maps 1:1.
        # cell values v > 0 represent rebus squares, where v corresponds to a solution key k=v-1 in the solutions map.
        # 0 values indicate non-rebus squares.
        self.table: list[int] = [0] * N

        # the solutions table is a map of rebus solution key k (an int) to the corresponding solution string,
        # eg 0:HEART;1:DIAMOND;17:CLUB;23:SPADE; k values need not be consecutive or in any order, but are
        # typically numbered sequentially starting from 0. When k values appear in the rebus table, they are
        # 1-indexed (ie v=k+1).
        self.solutions: dict[int, str] = {}

        # the fill table has the same number of entries as the grid and maps 1:1. Each cell value is a string
        # representing the user's current fill for that cell, eg "STAR". Non-filled cells and non-rebus cells
        # are empty strings.
        # When a cell is a rebus entry, the corresponding cell in puzzle.fill will often be set to the first
        # letter of the rebus, eg 'S' for "STAR".
        self.fill: list[str] = []

        # parse rebus data
        if Extensions.Rebus in self.puzzle.extensions:
            rebus_data = self.puzzle.extensions[Extensions.Rebus]
            self.table = parse_bytes(rebus_data)

        if Extensions.RebusSolutions in self.puzzle.extensions:
            raw_solution_data = self.puzzle.extensions[Extensions.RebusSolutions]
            solutions_str = raw_solution_data.decode(puzzle.encoding)
            self.solutions = {
                int(item[0]): item[1]
                for item in parse_dict(solutions_str).items()
            }

        if Extensions.RebusFill in self.puzzle.extensions:
            s = PuzzleBuffer(self.puzzle.extensions[Extensions.RebusFill], encoding=puzzle.encoding)
            fill = []
            while s.can_read():
                fill.append(s.read_string())
            self.fill = (fill + [''] * N)[:N]
        else:
            self.fill = [''] * N

    def has_rebus(self) -> bool:
        return Extensions.Rebus in self.puzzle.extensions or any(self.table)

    def is_rebus_square(self, index: int) -> bool:
        return self.table[index] > 0

    def get_rebus_squares(self) -> list[int]:
        return [i for i, k in enumerate(self.table) if k > 0]

    def add_rebus_squares(self, squares: int | list[int], solution: str) -> None:
        if isinstance(squares, int):
            squares = [squares]

        k = self.add_rebus_solution(solution)
        for i in squares:
            self.table[i] = k + 1  # rebus value is 1-indexed because 0 is reserved for non-rebus squares

    def add_rebus_solution(self, solution: str) -> int:
        k = next((i for i, s in self.solutions.items() if s == solution), -1)
        if k < 0:
            k = len(self.solutions)  # add to end of solutions
            self.solutions[k] = solution
        return k

    def check_rebus_fill(self, index: int) -> bool:
        if self.is_rebus_square(index):
            solution = self.get_rebus_solution(index)
            fill = self.get_rebus_fill(index)
            return solution == fill
        return False

    def get_rebus_solution(self, index: int) -> str | None:
        if self.is_rebus_square(index):
            # rebus value is 1-indexed because 0 is reserved for non-rebus squares
            # so we need to subtract 1 to get the correct solution from the map
            return self.solutions[self.table[index] - 1]
        return None

    def set_rebus_solution(self, index: int, solution: str) -> None:
        if self.is_rebus_square(index):
            solution_index = self.add_rebus_solution(solution)
            self.table[index] = solution_index + 1

    def get_rebus_fill(self, index: int) -> str | None:
        if self.is_rebus_square(index):
            return self.fill[index] or None
        return None

    def remove_rebus_squares(self, squares: int | list[int]) -> None:
        if isinstance(squares, int):
            squares = [squares]

        for i in squares:
            self.table[i] = 0
            self._dirty = True

    def remove_rebus_solution(self, solution: str | int) -> None:
        if isinstance(solution, str):
            k = next((i for i, s in self.solutions.items() if s == solution), -1)
        else:
            k = solution
        if k >= 0:
            del self.solutions[k]
            for i, v in enumerate(self.table):
                if v == k + 1:  # rebus value is 1-indexed because 0 is reserved for non-rebus squares
                    self.table[i] = 0
            self._dirty = True

    def set_rebus_fill(self, index: int, value: str) -> None:
        if self.is_rebus_square(index):
            self.fill[index] = value

    def save(self) -> None:
        if self.has_rebus():
            self.puzzle.extensions[Extensions.Rebus] = pack_bytes(self.table)
            if self.solutions:
                self.puzzle.extensions[Extensions.RebusSolutions] = self.puzzle.encode(dict_to_string(self.solutions))
            else:
                self.puzzle.extensions.pop(Extensions.RebusSolutions, None)
            if any(self.fill) or Extensions.RebusFill in self.puzzle.extensions:
                s = PuzzleBuffer(encoding=self.puzzle.encoding)
                for cell_fill in self.fill:
                    s.write_string(cell_fill)
                self.puzzle.extensions[Extensions.RebusFill] = s.tobytes()
            else:
                self.puzzle.extensions.pop(Extensions.RebusFill, None)
        elif self._dirty:
            self.puzzle.extensions.pop(Extensions.Rebus, None)
            self.puzzle.extensions.pop(Extensions.RebusSolutions, None)
            self.puzzle.extensions.pop(Extensions.RebusFill, None)


class Markup(PuzzleHelper):
    def __init__(self, puzzle: Puzzle) -> None:
        self.puzzle = puzzle
        self._dirty = False  # track whether there are unsaved changes to the markup helper that need to be committed
        markup_data = self.puzzle.extensions.get(Extensions.Markup, b'')
        self.markup = parse_bytes(markup_data) or [0] * (self.puzzle.width * self.puzzle.height)

    def clear_markup_squares(self, indices: list[int] | int, markup_types: list[GridMarkup] | GridMarkup | None = None) -> None:  # noqa: E501
        if isinstance(indices, int):
            indices = [indices]
        markup_mask = sum(markup_types) if isinstance(markup_types, list) else markup_types if markup_types else 0xff
        for i in indices:
            self.markup[i] &= ~markup_mask
            self._dirty = True

    def has_markup(self, markup_types: list[GridMarkup] | GridMarkup | None = None) -> bool:
        markup_mask = sum(markup_types) if isinstance(markup_types, list) else markup_types if markup_types else 0xff
        return any(bool(b & markup_mask) for b in self.markup)

    def get_markup_squares(self, markup_types: list[GridMarkup] | GridMarkup | None = None) -> list[int]:
        markup_mask = sum(markup_types) if isinstance(markup_types, list) else markup_types if markup_types else 0xff
        return [i for i, b in enumerate(self.markup) if b & markup_mask]

    def is_markup_square(self, index: int, markup_types: list[GridMarkup] | GridMarkup | None = None) -> bool:
        markup_mask = sum(markup_types) if isinstance(markup_types, list) else markup_types if markup_types else 0xff
        return bool(self.markup[index] & markup_mask)

    def set_markup_squares(self, indices: list[int] | int, markup_type: list[GridMarkup] | GridMarkup | None = None) -> None:
        if isinstance(indices, int):
            indices = [indices]
        markup_mask = sum(markup_type) if isinstance(markup_type, list) else markup_type if markup_type else 0xff
        for i in indices:
            self.markup[i] |= markup_mask

    def save(self) -> None:
        if self.has_markup():
            self.puzzle.extensions[Extensions.Markup] = pack_bytes(self.markup)
        elif self._dirty:
            self.puzzle.extensions.pop(Extensions.Markup, None)


class TimerStatus(IntEnum):
    Running = 0
    Stopped = 1


class Timer(PuzzleHelper):
    def __init__(self, puzzle: Puzzle) -> None:
        self.puzzle = puzzle
        timer_data = self.puzzle.extensions.get(Extensions.Timer, b'0,1')
        elapsed_str, status_str = timer_data.decode().split(',')

        self.elapsed_seconds = int(elapsed_str)
        self.status = TimerStatus(int(status_str))

    def is_running(self) -> bool:
        return self.status == TimerStatus.Running

    def is_stopped(self) -> bool:
        return self.status == TimerStatus.Stopped

    def save(self) -> None:
        self.puzzle.extensions[Extensions.Timer] = f'{self.elapsed_seconds},{self.status}'.encode()


# helper functions for cksums and scrambling
def data_cksum(data: bytes, cksum: int = 0) -> int:
    for b in data:
        # right-shift one with wrap-around
        lowbit = (cksum & 0x0001)
        cksum = (cksum >> 1)
        if lowbit:
            cksum = (cksum | 0x8000)

        # then add in the data and clear any carried bit past 16
        cksum = (cksum + b) & 0xffff

    return cksum


def replace_chars(s: str, chars: str, replacement: str = '') -> str:
    for ch in chars:
        s = s.replace(ch, replacement)
    return s


def scramble_solution(solution: str, width: int, height: int, key: int, ignore_chars: str = BLACKSQUARE) -> str:
    sq = square(solution, width, height)
    data = restore(sq, scramble_string(replace_chars(sq, ignore_chars), key))
    return square(data, height, width)


def scramble_string(s: str, key: int) -> str:
    """
    s is the puzzle's solution in column-major order, omitting black squares:
    i.e. if the puzzle is:
        C A T
        # # A
        # # R
    solution is CATAR


    Key is a 4-digit number in the range 1000 <= key <= 9999

    """
    digits = key_digits(key)
    for k in digits:          # foreach digit in the key
        s = shift(s, digits)  # for each char by each digit in the key in sequence
        s = s[k:] + s[:k]  # cut the sequence around the key digit
        s = shuffle(s)     # do a 1:1 shuffle of the 'deck'

    return s


def unscramble_solution(scrambled: str, width: int, height: int, key: int, ignore_chars: str = BLACKSQUARE) -> str:
    # width and height are reversed here
    sq = square(scrambled, width, height)
    data = restore(sq, unscramble_string(replace_chars(sq, ignore_chars), key))
    return square(data, height, width)


def unscramble_string(s: str, key: int) -> str:
    digits = key_digits(key)
    l = len(s)  # noqa: E741
    for k in digits[::-1]:
        s = unshuffle(s)
        s = s[l-k:] + s[:l-k]
        s = unshift(s, digits)

    return s


def scrambled_cksum(scrambled: str, width: int, height: int, ignore_chars: str = BLACKSQUARE, encoding: str = ENCODING) -> int:
    data = replace_chars(square(scrambled, width, height), ignore_chars)
    return data_cksum(data.encode(encoding, ENCODING_ERRORS))


def key_digits(key: int) -> list[int]:
    return [int(c) for c in str(key).zfill(4)]


def square(data: str, w: int, h: int) -> str:
    aa = [data[i:i+w] for i in range(0, len(data), w)]
    return ''.join(
        [''.join([aa[r][c] for r in range(0, h)]) for c in range(0, w)]
    )


def shift(s: str, key: list[int]) -> str:
    atoz = string.ascii_uppercase
    return ''.join(
        atoz[(atoz.index(c) + key[i % len(key)]) % len(atoz)]
        for i, c in enumerate(s)
    )


def unshift(s: str, key: list[int]) -> str:
    return shift(s, [-k for k in key])


def shuffle(s: str) -> str:
    mid = int(math.floor(len(s) / 2))
    items = functools.reduce(operator.add, zip(s[mid:], s[:mid]))
    return ''.join(items) + (s[-1] if len(s) % 2 else '')


def unshuffle(s: str) -> str:
    return s[1::2] + s[::2]


def restore(s: str, t: Iterable[str]) -> str:
    """
    s is the source string, it can contain '.'
    t is the target, it's smaller than s by the number of '.'s in s

    Each char in s is replaced by the corresponding
    char in t, jumping over '.'s in s.

    >>> restore('ABC.DEF', 'XYZABC')
    'XYZ.ABC'
    """
    t = (c for c in t)
    return ''.join(next(t) if not is_blacksquare(c) else c for c in s)


def is_blacksquare(c: str | int) -> bool:
    if isinstance(c, int):
        c = chr(c)
    return c in [BLACKSQUARE, BLACKSQUARE2]


#
# functions for parsing / serializing primitives
#


def parse_bytes(s: bytes) -> list[int]:
    return list(struct.unpack('B' * len(s), s))


def pack_bytes(a: list[int]) -> bytes:
    return struct.pack('B' * len(a), *a)


# dict string format is k1:v1;k2:v2;...;kn:vn;
# (for whatever reason there's a trailing ';')
def parse_dict(s: str) -> dict[str, str]:
    return dict(p.split(':', 1) for p in s.split(';') if ':' in p)


def dict_to_string(d: dict[int, str]) -> str:
    # Across Lite format right-aligns keys in a 2-char field: ' 0:VAL;', '13:VAL;'
    return ';'.join(f'{k:>2}:{v}' for k, v in d.items()) + ';'


def from_text_format(s: str) -> Puzzle:
    d = text_file_as_dict(s)

    if 'ACROSS PUZZLE' in d:
        # file_version = 'v1'
        pass
    elif 'ACROSS PUZZLE v2' in d:
        # file_version = 'v2'
        pass
    else:
        raise PuzzleFormatError('Not a valid Across Lite text puzzle')

    p = Puzzle()
    across_clues: list[str] = []
    down_clues: list[str] = []
    if 'TITLE' in d:
        p.title = d['TITLE']
    if 'AUTHOR' in d:
        p.author = d['AUTHOR']
    if 'COPYRIGHT' in d:
        p.copyright = d['COPYRIGHT']
    if 'SIZE' in d:
        w, h = d['SIZE'].split('x')
        p.width = int(w)
        p.height = int(h)
    # parse REBUS section before GRID — markers in the grid reference it
    # format: marker:EXTENDED_SOLUTION:SHORT_CHAR (one per line)
    # optional flag line: MARK; (circles all lowercase-letter cells in the grid)
    rebus_map: dict[str, tuple[str, str]] = {}  # marker char -> (extended_solution, short_char)
    mark_flag = False
    if 'REBUS' in d:
        for line in d['REBUS'].splitlines():
            line = line.strip()
            if not line:
                continue
            if ':' not in line:
                # flag line, e.g. "MARK;"
                if 'MARK' in [f.strip().upper() for f in line.split(';') if f.strip()]:
                    mark_flag = True
            else:
                parts = line.split(':')
                marker = parts[0]
                extended = parts[1] if len(parts) > 1 else ''
                short = parts[2] if len(parts) > 2 else (extended[0] if extended else marker)
                if marker:
                    rebus_map[marker] = (extended, short)

    rebus_cells: dict[int, str] = {}  # cell index -> extended solution
    mark_cells: list[int] = []       # cell indices to be circled (MARK flag)
    if 'GRID' in d:
        solution_lines = d['GRID'].splitlines()
        raw = ''.join(line.strip() for line in solution_lines if line.strip())
        if rebus_map or mark_flag:
            solution_chars: list[str] = []
            for i, c in enumerate(raw):
                if c in rebus_map:
                    extended, short = rebus_map[c]
                    solution_chars.append(short)
                    rebus_cells[i] = extended
                elif mark_flag and c.islower() and not is_blacksquare(c):
                    solution_chars.append(c.upper())
                    mark_cells.append(i)
                else:
                    solution_chars.append(c)
            p.solution = ''.join(solution_chars)
        else:
            p.solution = raw
    if 'ACROSS' in d:
        across_clues.extend(line.strip() for line in d['ACROSS'].splitlines() if line.strip())
    if 'DOWN' in d:
        down_clues.extend(line.strip() for line in d['DOWN'].splitlines() if line.strip())
    if 'NOTEPAD' in d:
        p.notes = d['NOTEPAD']

    if p.solution:
        if BLACKSQUARE2 in p.solution:
            p.puzzletype = PuzzleType.Diagramless
        p.fill = ''.join(c if is_blacksquare(c) else BLANKSQUARE for c in p.solution)
        across, down = get_grid_numbering(p.fill, p.width, p.height)
        # we have to match puzfile's expected clue ordering or we won't be able to
        # write the puzzle out as a valid .puz file
        p.clues = [''] * (len(across) + len(down))
        for i in range(len(across)):
            clue = across_clues[i] if i < len(across_clues) else ''
            across[i]['clue'] = clue
            p.clues[across[i]['clue_index']] = clue
        for i in range(len(down)):
            clue = down_clues[i] if i < len(down_clues) else ''
            down[i]['clue'] = clue
            p.clues[down[i]['clue_index']] = clue

        if rebus_cells:
            r = p.rebus()
            for i, extended in rebus_cells.items():
                k = next((k for k, v in r.solutions.items() if v == extended), None)
                if k is None:
                    k = len(r.solutions)
                    r.solutions[k] = extended
                r.table[i] = k + 1
        if mark_cells:
            p.markup().set_markup_squares(mark_cells, GridMarkup.Circled)

    return p


def text_file_as_dict(s: str) -> dict[str, str]:
    d: dict[str, str] = {}
    k = ''
    v: list[str] = []
    for line in s.splitlines():
        line = line.strip()
        if line.startswith('<') and line.endswith('>'):
            if k:
                d[k] = '\n'.join(v)
            k = line[1:-1]
            v = []
        else:
            v.append(line)

    if k:
        d[k] = '\n'.join(v)
    return d


def to_text_format(p: Puzzle, text_version: str = 'v1') -> str:
    TAB = '\t'  # most lines begin indented with whitespace
    lines = []

    rebus = p.rebus() if p.has_rebus() else None
    has_rebus = rebus is not None and rebus.has_rebus()

    markup = p.markup() if p.has_markup() else None
    has_mark = markup is not None and markup.has_markup([GridMarkup.Circled])

    # rebus and MARK flag require v2 format; auto-upgrade if needed
    if (has_rebus or has_mark) and text_version == 'v1':
        text_version = 'v2'

    if text_version == 'v1':
        lines.append('<ACROSS PUZZLE>')
    elif text_version:
        lines.append(f'<ACROSS PUZZLE {text_version}>')
    else:
        raise ValueError("invalid text_version")

    lines.append('<TITLE>')
    lines.append(TAB + p.title)
    lines.append('<AUTHOR>')
    lines.append(TAB + p.author)
    lines.append('<COPYRIGHT>')
    lines.append(TAB + p.copyright)
    lines.append('<SIZE>')
    lines.append(TAB + f'{p.width}x{p.height}')

    # assign a single-char marker to each unique rebus solution
    # digits 1-9 then lowercase a-z, matching the v2 spec convention
    solution_to_marker: dict[str, str] = {}
    if has_rebus:
        assert rebus is not None
        _marker_chars = [str(i) for i in range(1, 10)] + list('abcdefghijklmnopqrstuvwxyz')
        for idx, solution in enumerate(rebus.solutions.values()):
            if idx < len(_marker_chars):
                solution_to_marker[solution] = _marker_chars[idx]

    lines.append('<GRID>')
    for row_idx in range(p.height):
        row = ''
        for col_idx in range(p.width):
            i = row_idx * p.width + col_idx
            if rebus and rebus.is_rebus_square(i):
                sol = rebus.get_rebus_solution(i)
                row += solution_to_marker.get(sol or '', p.solution[i])
            elif has_mark and markup and markup.is_markup_square(i, [GridMarkup.Circled]):
                row += p.solution[i].lower()
            else:
                row += p.solution[i]
        lines.append(TAB + row)

    if has_rebus or has_mark:
        lines.append('<REBUS>')
        if has_mark:
            lines.append(TAB + 'MARK;')
        if has_rebus:
            assert rebus is not None
            for solution, marker in solution_to_marker.items():
                # short_char is whatever single letter is stored in p.solution at a rebus square
                short_char = solution[0]  # fallback
                for i in range(p.width * p.height):
                    if rebus.is_rebus_square(i) and rebus.get_rebus_solution(i) == solution:
                        short_char = p.solution[i]
                        break
                lines.append(TAB + f'{marker}:{solution}:{short_char}')

    # get clues in across/down order
    numbering = p.clue_numbering()
    lines.append('<ACROSS>')
    for clue in numbering.across:
        lines.append(TAB + (clue['clue'] or ''))
    lines.append('<DOWN>')
    for clue in numbering.down:
        lines.append(TAB + (clue['clue'] or ''))

    lines.append('<NOTEPAD>')
    lines.append(p.notes)  # no tab here, idk why

    return '\n'.join(lines)
