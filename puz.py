import struct
import logging
import string
import operator

header_format = '''<
             H 11s        xH
             Q       4s  2sH
             12s         BBH
             H H '''

header_cksum_format = '<BBH H H '
maskstring = 'ICHEATED'
ACROSSDOWN = 'ACROSS&DOWN'
BLACKSQUARE = '.'

extension_header_format = '< 4s  H H '

def enum(**enums):
    return type('Enum', (), enums)

PuzzleType = enum(Normal=0x0001,
                  Diagramless=0x0401)

# the following diverges from the documentation but works for the files I've tested
SolutionState = enum(Unlocked=0x0000,      # solution is available in plaintext
                     Locked=0x0004)        # solution is locked (scrambled) with a key

GridMarkup = enum(Default=0x00,              # ordinary grid cell
                  PreviouslyIncorrect=0x10,  # marked incorrect at some point
                  Incorrect=0x20,            # currently showing incorrect
                  Revealed=0x40,             # user got a hint
                  Circled=0x80)              # circled

# refer to Extensions as Extensions.Rebus, Extensions.Markup
Extensions = enum(Rebus='GRBS',             # grid of rebus indices: 0 for non-rebus; i+1 for key i into RebusSolutions map
                  RebusSolutions='RTBL',    # map of rebus solution entries eg 0:HEART;1:DIAMOND;17:CLUB;23:SPADE;
                  RebusFill='RUSR',         # user's rebus entries
                  Timer='LTIM',             # timer state: 'a,b' where a is the number of seconds elapsed and b is a boolean (0,1) for whether the timer is running
                  Markup='GEXT')            # grid cell markup: previously incorrect: 0x10; currently incorrect: 0x20, hinted: 0x40, circled: 0x80

def read(filename):
    """Read a .puz file and return the Puzzle object
    throws PuzzleFormatError if there's any problem with the file format
    """
    f = open(filename, 'rb')
    try:
        puz = Puzzle()
        puz.load(f.read())
        return puz
    finally:
        f.close()

def load(data):
    """Read .puz file data and return the Puzzle object
    throws PuzzleFormatError if there's any problem with the file format
    """
    puz = Puzzle()
    puz.load(data)
    return puz


class PuzzleFormatError:
    """Indicates a format error in the .puz file
    May be thrown due to invalid headers, invalid checksum validation, or other format issues
    """
    def __init__(self, message=''):
        self.message = message

class Puzzle:
    """Represents a puzzle
    """
    def __init__(self):
        """Initializes a blank puzzle
        """
        self.preamble = ''
        self.postscript = ''
        self.title = ''
        self.author = ''
        self.copyright = ''
        self.width = 0
        self.height = 0
        self.version = '1.3'
        self.fileversion = '1.3\0' # default
        # these are bytes that might be unused
        self.unk1 = '\0' * 2
        self.unk2 = '\0' * 12
        self.scrambled_cksum = 0
        self.fill = ''
        self.solution = ''
        self.clues = []
        self.notes = ''
        self.extensions = {}
        self._extensions_order = [] # so that we can round-trip values in order
        self.puzzletype = PuzzleType.Normal
        self.solution_state = SolutionState.Unlocked
        self.helpers = {} # add-ons like Rebus and Markup

    def load(self, data):
        s = PuzzleBuffer(data)

        # advance to start - files may contain some data before the start of the puzzle
        # use the ACROSS&DOWN magic string as a waypoint
        # save the preamble for round-tripping
        if not s.seek_to(ACROSSDOWN, -2):
            raise PuzzleFormatError("Data does not appear to represent a puzzle. Are you sure you didn't intend to use read?")

        self.preamble = s.data[:s.pos]

        (cksum_gbl, acrossDown, cksum_hdr, cksum_magic,
         self.fileversion, self.unk1, # since we don't know the role of these bytes, just round-trip them
         self.scrambled_cksum, self.unk2,
         self.width, self.height, numclues, self.puzzletype, self.solution_state
        ) = s.unpack(header_format)

        self.version = self.fileversion[:3]
        self.solution = s.read(self.width * self.height)
        self.fill = s.read(self.width * self.height)

        self.title = s.read_string()
        self.author = s.read_string()
        self.copyright = s.read_string()

        self.clues = [s.read_string() for i in xrange(0, numclues)]
        self.notes = s.read_string()

        ext_cksum = {}
        while s.can_unpack(extension_header_format):
            code, length, cksum = s.unpack(extension_header_format)
            ext_cksum[code] = cksum
            # extension data is represented as a null-terminated string, but since the data can contain nulls
            # we can't use read_string
            self.extensions[code] = s.read(length)
            s.read(1) # extensions have a trailing byte
            # save the codes in order for round-tripping
            self._extensions_order.append(code)

        # sometimes there's some extra garbage at the end of the file, usually \r\n
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
                raise PuzzleFormatError('extension %s checksum does not match' % code)

    def save(self, filename):
        f = open(filename, 'wb')
        try:
            f.write(self.tostring())
        finally:
            f.close()

    def tostring(self):
        s = PuzzleBuffer()
        # commit any changes from helpers
        for h in self.helpers.values():
            if 'save' in dir(h):
                h.save()

        # include any preamble text we might have found on read
        s.write(self.preamble)

        s.pack(header_format,
                self.global_cksum(), ACROSSDOWN, self.header_cksum(), self.magic_cksum(),
                self.fileversion, self.unk1, self.scrambled_cksum,
                self.unk2, self.width, self.height,
                len(self.clues), self.puzzletype, self.solution_state)

        s.write(self.solution)
        s.write(self.fill)

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
                s.pack(extension_header_format, code, len(data), data_cksum(data))
                s.write(data + '\0')

        for code, data in ext.items():
            s.pack(extension_header_format, code, len(data), data_cksum(data))
            s.write(data + '\0')

        s.write(self.postscript)

        return s.tostring()

    def has_rebus(self):
        return self.rebus().has_rebus()

    def rebus(self):
        return self.helpers.setdefault('rebus', Rebus(self))

    def has_markup(self):
        return self.markup().has_markup()

    def markup(self):
        return self.helpers.setdefault('markup', Markup(self))

    def clue_numbering(self):
        return self.helpers.setdefault('clues', DefaultClueNumbering(self.fill, self.clues, self.width, self.height))

    def is_solution_locked(self):
        return bool(self.solution_state != SolutionState.Unlocked)

    def unlock_solution(self, key):
        if self.is_solution_locked():
            unscrambled = unscramble_solution(self.solution, self.width, self.height, key)
            if not self.check_answers(unscrambled):
                return False

            # clear the scrambled bit and cksum
            self.solution = unscrambled
            self.scrambled_cksum = 0
            self.solution_state = SolutionState.Unlocked

        return True

    def lock_solution(self, key):
        if not self.is_solution_locked():
            # set the scrambled bit and cksum
            self.scrambled_cksum = scrambled_cksum(self.solution, self.width, self.height)
            self.solution_state = SolutionState.Locked
            self.solution = scramble_solution(self.solution, self.width, self.height, key)

    def check_answers(self, fill):
        if self.is_solution_locked():
            return scrambled_cksum(fill, self.width, self.height) == self.scrambled_cksum
        else:
            return fill == self.solution

    def header_cksum(self, cksum=0):
        return data_cksum(struct.pack(header_cksum_format,
            self.width, self.height, len(self.clues), self.puzzletype, self.solution_state), cksum)

    def text_cksum(self, cksum=0):
        # for the checksum to work these fields must be added in order with
        # null termination, followed by all non-empty clues without null
        # termination, followed by notes (but only for version 1.3)
        if self.title:
            cksum = data_cksum(self.title + '\0', cksum)
        if self.author:
            cksum = data_cksum(self.author + '\0', cksum)
        if self.copyright:
            cksum = data_cksum(self.copyright + '\0', cksum)

        for clue in self.clues:
            if clue:
                cksum = data_cksum(clue, cksum)

        # notes included in global cksum only in v1.3 of format
        if self.version == '1.3' and self.notes:
            cksum = data_cksum(self.notes + '\0', cksum)

        return cksum

    def global_cksum(self):
        cksum = self.header_cksum()
        cksum = data_cksum(self.solution, cksum)
        cksum = data_cksum(self.fill, cksum)
        cksum = self.text_cksum(cksum)
        # extensions do not seem to be included in global cksum
        return cksum

    def magic_cksum(self):
        cksums = [
            self.header_cksum(),
            data_cksum(self.solution),
            data_cksum(self.fill),
            self.text_cksum()
        ]

        cksum_magic = 0
        for (i, cksum) in enumerate(reversed(cksums)):
            cksum_magic <<= 8
            cksum_magic |= (ord(maskstring[len(cksums) - i - 1]) ^ (cksum & 0x00ff))
            cksum_magic |= (ord(maskstring[len(cksums) - i - 1 + 4]) ^ (cksum >> 8)) << 32

        return cksum_magic


class PuzzleBuffer:
    """PuzzleBuffer class
    wraps a data buffer ('' or []) and provides .puz-specific methods for
    reading and writing data
    """
    def __init__(self, data=None, enc='ISO-8859-1'):
        self.data = data or []
        self.enc = enc
        self.pos = 0

    def can_read(self, bytes=1):
        return self.pos + bytes <= len(self.data)

    def length(self):
        return len(self.data)

    def read(self, bytes):
        start = self.pos
        self.pos += bytes
        return self.data[start:self.pos]

    def read_to_end(self):
        start = self.pos
        self.pos = self.length()
        return self.data[start:self.pos]

    def read_string(self):
        return self.read_until('\0')

    def read_until(self, c):
        start = self.pos
        self.seek_to(c, 1) # read past
        return unicode(self.data[start:self.pos-1], self.enc)

    def seek(self, pos):
        self.pos = pos

    def seek_to(self, s, offset=0):
        try:
            self.pos = self.data.index(s, self.pos) + offset
            return True
        except ValueError:
            # s not found, advance to end
            self.pos = self.length()
            return False

    def write(self, s):
        self.data.append(s)

    def write_string(self, s):
        s = s or ''
        self.data.append(s.encode(self.enc) + '\0')

    def pack(self, format, *values):
        self.data.append(struct.pack(format, *values))

    def can_unpack(self, format):
        return self.can_read(struct.calcsize(format))

    def unpack(self, format):
        start = self.pos
        try:
            res = struct.unpack_from(format, self.data, self.pos)
            self.pos += struct.calcsize(format)
            return res
        except struct.error:
            raise PuzzleFormatError('could not unpack values at %d for format %s' % (start, format))

    def tostring(self):
        return ''.join(self.data)


# clue numbering helper

class DefaultClueNumbering:
    def __init__(self, grid, clues, width, height):
        self.grid = grid
        self.clues = clues
        self.width = width
        self.height = height

        # compute across & down
        a = []
        d = []
        c = 0
        n = 1
        for i in xrange(0, len(grid)):
            if not is_blacksquare(grid[i]):
                lastc = c
                if (self.col(i) == 0 or is_blacksquare(grid[i - 1])) and self.len_across(i) > 1:
                    clue = {'num': n, 'clue': clues[c], 'cell': i, 'len': self.len_across(i) }
                    a.append(clue)
                    c += 1
                if (self.row(i) == 0 or is_blacksquare(grid[i - width])) and self.len_down(i) > 1:
                    clue = {'num': n, 'clue': clues[c], 'cell': i, 'len': self.len_down(i) }
                    d.append(clue)
                    c += 1
                if c > lastc:
                    n += 1

        self.across = a
        self.down = d

    def col(self, index):
        return index % self.width

    def row(self, index):
        return index / self.width

    def len_across(self, index):
        for c in xrange(0, self.width - self.col(index)):
            if is_blacksquare(self.grid[index + c]):
                return c
        return c + 1

    def len_down(self, index):
        for c in xrange(0, self.height - self.row(index)):
            if is_blacksquare(self.grid[index + c*self.width]):
                return c
        return c + 1

class Rebus:
    def __init__(self, puzzle):
        self.puzzle = puzzle
        # parse rebus data
        self.table = parse_bytes(self.puzzle.extensions.get(Extensions.Rebus, ''))
        self.solutions = dict(map(lambda p: (int(p[0]), p[1]), parse_dict(self.puzzle.extensions.get(Extensions.RebusSolutions, '')).items()))
        self.fill = dict(map(lambda p: (int(p[0]), p[1]), parse_dict(self.puzzle.extensions.get(Extensions.RebusFill, '')).items()))

    def has_rebus(self):
        return Extensions.Rebus in self.puzzle.extensions

    def is_rebus_square(self, index):
        return bool(self.table[index])

    def get_rebus_squares(self):
        return [i for i, b in enumerate(self.table) if b]

    def get_rebus_solution(self, index):
        return self.solutions[self.table[index] - 1] if self.is_rebus_square(index) else None

    def get_rebus_fill(self, index):
        return self.fill[self.table[index] - 1] if self.is_rebus_square(index) else None

    def set_rebus_fill(self, index, value):
        if self.is_rebus_square(index):
            self.fill[self.table[index] - 1] = value

    def save(self):
        if self.has_rebus():
            # commit changes back to puzzle.extensions
            self.puzzle.extensions[Extensions.Rebus] = bytes_to_string(self.table)
            self.puzzle.extensions[Extensions.RebusSolutions] = dict_to_string(self.solutions)
            self.puzzle.extensions[Extensions.RebusFill] = dict_to_string(self.fill)

class Markup:
    def __init__(self, puzzle):
        self.puzzle = puzzle
        # parse markup data
        self.markup = parse_bytes(self.puzzle.extensions.get(Extensions.Markup, ''))

    def has_markup(self):
        return any(bool(b) for b in self.markup)

    def get_markup_squares(self):
        return [i for i,b in enumerate(self.markup) if b]

    def is_markup_square(self, index):
        return bool(self.table[index])

    def save(self):
        if self.has_markup():
            self.puzzle.extensions[Extensions.Markup] = bytes_to_string(self.markup)

# helper functions for cksums and scrambling
def data_cksum(data, cksum=0):
    for c in data:
        b = ord(c)
        # right-shift one with wrap-around
        lowbit = (cksum & 0x0001)
        cksum = (cksum >> 1)
        if lowbit: cksum = (cksum | 0x8000)

        # then add in the data and clear any carried bit past 16
        cksum = (cksum + b) & 0xffff

    return cksum

def scramble_solution(solution, width, height, key):
    sq = square(solution, width, height)
    return square(restore(sq, scramble_string(sq.replace(BLACKSQUARE, ''), key)), height, width)

def scramble_string(s, key):
    """
    s is the puzzle's solution in column-major order, omitting black squares:
    i.e. if the puzzle is:
        C A T
        # # A
        # # R
    solution is CATAR


    Key is a 4-digit number in the range 1000 <= key <= 9999

    """
    key = key_digits(key)
    for k in key: # foreach digit in the key
        s = shift(s, key)  # xform each char by each digit in the key in sequence
        s = s[k:] + s[:k]  # cut the sequence around the key digit
        s = shuffle(s)     # do a 1:1 shuffle of the 'deck'

    return s

def unscramble_solution(scrambled, width, height, key):
    # width and height are reversed here
    sq = square(scrambled, width, height)
    return square(restore(sq, unscramble_string(sq.replace(BLACKSQUARE, ''), key)), height, width)

def unscramble_string(s, key):
    key = key_digits(key)
    l = len(s)
    for k in key[::-1]:
        s = unshuffle(s)
        s = s[l-k:] + s[:l-k]
        s = unshift(s, key)

    return s

def scrambled_cksum(scrambled, width, height):
    return data_cksum(square(scrambled, width, height).replace(BLACKSQUARE, ''))

def key_digits(key):
    return [int(c) for c in str(key).zfill(4)]

def square(data, w, h):
    aa = [data[i:i+w] for i in range(0, len(data), w)]
    return ''.join([''.join([aa[r][c] for r in range(0, h)]) for c in range(0, w)])

def shift(s, key):
    atoz = string.uppercase
    return ''.join(atoz[(atoz.index(c) + key[i % len(key)]) % len(atoz)] for i, c in enumerate(s))

def unshift(s, key):
    return shift(s, [-k for k in key])

def shuffle(s):
    mid = len(s) / 2
    return ''.join(reduce(operator.add, zip(s[mid:], s[:mid]))) + (s[-1] if len(s) % 2 else '')

def unshuffle(s):
    return s[1::2] + s[::2]

def restore(s, t):
    """
    s is the source string, it can contain '.'
    t is the target, it's smaller than s by the number of '.'s in s
    each char in s is replaced by the corresponding char in t, jumping over '.'s in s

    >>> restore('ABC.DEF', 'XYZABC')
    'XYZ.ABC'
    """
    t = (c for c in t)
    return ''.join(t.next() if not is_blacksquare(c) else c for c in s)

def is_blacksquare(c):
    return c == BLACKSQUARE

#
# functions for parsing / serializing primitives
#

def parse_bytes(s):
    return list(struct.unpack('B' * len(s), s))

def bytes_to_string(a):
    return struct.pack('B' * len(a), *a)

# dict string format is k1:v1;k2:v2;...;kn:vn;
# (for whatever reason there's a trailing ';')
def parse_dict(s):
    return dict(p.split(':') for p in s.split(';') if ':' in p)

def dict_to_string(d):
    return ';'.join(':'.join(map(str, [k,v])) for k,v in d.items()) + ';'
