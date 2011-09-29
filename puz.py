import struct
import logging

header_format = '''<
             H 11s        xH
             Q       3s 17s
                         BBH
             4s'''

header_cksum_format = '<BBH4s'
maskstring = 'ICHEATED'
ACROSSDOWN = 'ACROSS&DOWN'

extension_header_format = '''< 4s  H H'''

flags_normal = '\1\0\0\0'

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
        self.title = ''
        self.author = ''
        self.copyright = ''
        self.width = 0
        self.height = 0
        self.fileversion = '1.3' # default
        # these are bytes that might be unused
        self.unk = '\0' * 17
        self.fill = ''
        self.answers = ''
        self.clues = []
        self.notes = ''
        self.extensions = {}
        self._extensions_order = [] # so that we can round-trip values in order for test purposes
        self.flags = flags_normal

    def load(self, data):
        s = PuzzleBuffer(data)
        
        # advance to start - files may contain some data before the start of the puzzle
        # use the ACROSS&DOWN magic string as a waypoint
        # save the preamble for round-tripping
        s.seek_to(ACROSSDOWN, -2)
        self.preamble = s.data[:s.pos]
        
        (cksum_gbl, acrossDown, cksum_hdr, cksum_magic,
         self.fileversion, self.unk, # since we don't know the role of these bytes, just round-trip them
         self.width, self.height, numclues, self.flags
        ) = s.unpack(header_format)
        
        if acrossDown != ACROSSDOWN:
            raise PuzzleFormatError('invalid puz file: does not contain correct header')

        self.answers = s.read(self.width * self.height)
        self.fill = s.read(self.width * self.height)

        self.title = s.read_string()
        self.author = s.read_string()
        self.copyright = s.read_string()
        
        self.clues = [s.read_string() for i in xrange(0, numclues)]
        self.notes = s.read_string()
        
        ext_cksum = {}
        while s.can_read():
            code, length, cksum = s.unpack(extension_header_format)
            ext_cksum[code] = cksum
            # extension data is represented as a null-terminated string, but since the data can contain nulls
            # we can't use read_string
            self.extensions[code] = s.read(length)
            s.read(1) # extensions have a trailing byte
            # save the codes in order for round-tripping
            self._extensions_order.append(code)

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
        # include any preamble text we might have found on read
        s.write(self.preamble)
        
        s.pack(header_format,
                self.global_cksum(), ACROSSDOWN, self.header_cksum(), self.magic_cksum(),
                self.fileversion, self.unk, self.width, self.height, 
                len(self.clues), self.flags)

        s.write(self.answers)
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
        
        return s.tostring()
  
    def header_cksum(self, cksum=0):
        return data_cksum(struct.pack(header_cksum_format, 
            self.width, self.height, len(self.clues), self.flags), cksum)
    
    def text_cksum(self, cksum=0):
        # for the checksum to work these fields must be added in order with
        # null termination, followed by all non-empty clues without null
        # termination, followed by notes (but only for fileversion 1.3)
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
        if self.fileversion == '1.3' and self.notes:
            cksum = data_cksum(self.notes + '\0', cksum)
        
        return cksum
        
    def global_cksum(self):
        cksum = self.header_cksum()
        cksum = data_cksum(self.answers, cksum)
        cksum = data_cksum(self.fill, cksum)
        cksum = self.text_cksum(cksum)
        # extensions do not seem to be included in global cksum
        return cksum
  
    def magic_cksum(self):
        cksums = [
            self.header_cksum(),
            data_cksum(self.answers),
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
  
    def can_read(self):
        return self.pos < len(self.data)
  
    def length(self):
        return len(self.data)
  
    def read(self, bytes):
        start = self.pos
        self.pos += bytes
        return self.data[start : self.pos]
  
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
        except ValueError:
            # s not found, advance to end
            self.pos = self.length()
    
    def write(self, s):
        self.data.append(s)
    
    def write_string(self, s):
        s = s or ''
        self.data.append(s.encode(self.enc) + '\0')
    
    def pack(self, format, *values):
        self.data.append(struct.pack(format, *values))
  
    def unpack(self, format):
        res = struct.unpack_from(format, self.data, self.pos)
        self.pos += struct.calcsize(format)
        return res
        
    def tostring(self):
        return ''.join(self.data)


# helper functions for cksums
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

