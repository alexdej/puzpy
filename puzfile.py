import struct
import logging

# helper type for static-ish functions
class Static:
  def __init__(self, callable):
    self.__call__ = callable

class Puzzle:
  def read(data):
    puz = Puzzle()
    puz.readFrom(PuzzleReader(data, 'ISO-8859-1'))
    return puz
  read = Static(read)
    
  def readFrom(self, r):
    self.header = PuzzleHeader.read(r)
    
    self.length = self.header.width * self.header.height
    self.answers = r.readString(self.length)
    self.fill = r.readString(self.length)

    self.title = r.readUnicodeString()
    self.author = r.readUnicodeString()
    self.copyright = r.readUnicodeString()

    self.clues = [r.readUnicodeString() for i in xrange(0, self.header.numclues)]
    self.notes = r.readUnicodeString()
    
    self.extensions = []
    while r.canRead():
      self.extensions.append(PuzzleExtension.read(r))

    self.validate()
    
  def getData(self):
    self.updateChecksums()
  
    w = PuzzleWriter('ISO-8859-1')
    self.writeTo(w)
    return w.getData()
    
  def writeTo(self, w):
    self.header.writeTo(w)
    
    w.writeString(self.answers)
    w.writeString(self.fill)
    
    w.writeUnicodeString(self.title)
    w.writeUnicodeString(self.author)
    w.writeUnicodeString(self.copyright)
    
    for c in self.clues: 
      w.writeUnicodeString(c)
      
    w.writeUnicodeString(self.notes)
    
    for ext in self.extensions:
      ext.writeTo(w)
    
  def validate(self):
    cksum_gbl = self.calculateGlobalChecksum()
    cksum_magic = self.calculateMagicChecksum()

    values = {
      'cksum_gbl': [ self.header.cksum_gbl, cksum_gbl ],
      'cksum_magic': [ self.header.cksum_magic, cksum_magic ],
    }    
    
    for (k, v) in values.items():
      if v[0] != v[1]:
        logging.warning('cksum validation warning: %s values do not match [%s, %s]' % (k, v[0], v[1]))

  def updateChecksums(self):
    self.header.updateChecksum()
    self.header.cksum_gbl = self.calculateGlobalChecksum()
    self.header.cksum_magic = self.calculateMagicChecksum()
    
    for extension in self.extensions:
      extension.updateChecksum()

  def calculateGlobalChecksum(self):
    cksum = self.header.calculateChecksum()
    cksum = cksum_data(self.answers, cksum)
    cksum = cksum_data(self.fill, cksum)
    if self.title:
      cksum = cksum_data(self.title + '\0', cksum)
    if self.author:
      cksum = cksum_data(self.author + '\0', cksum)
    if self.copyright:
      cksum = cksum_data(self.copyright + '\0', cksum)
    
    for clue in self.clues:
      if clue:
        cksum = cksum_data(clue, cksum)

    # notes included in global cksum only in v1.3 of format
    if self.header.version == '1.3' and self.notes:
      cksum = cksum_data(self.notes + '\0', cksum)
    
    # extensions do not seem to be included in global cksum
    
    return cksum
    
  maskstring = 'ICHEATED'
  def calculateMagicChecksum(self):
    cksum_hdr = self.header.calculateChecksum()
    cksum_soln = cksum_data(self.answers)
    cksum_fill = cksum_data(self.fill)

    if self.title:
      cksum_text = cksum_data(self.title + '\0')
    if self.author:
      cksum_text = cksum_data(self.author + '\0', cksum_text)
    if self.copyright:
      cksum_text = cksum_data(self.copyright + '\0', cksum_text)
    for clue in self.clues:
      if clue:
        cksum_text = cksum_data(clue, cksum_text)

    # notes included in magic cksum only in v1.3 of format
    if self.header.version == '1.3' and self.notes:
      cksum_text = cksum_data(self.notes + '\0', cksum_text)
    
    # extensions do not seem to be included in magic cksum
    
    cksums = [cksum_hdr, cksum_soln, cksum_fill, cksum_text]
    
    cksum_magic = 0
    for i in xrange(3, -1, -1):
      cksum_magic <<= 8

      cksum_magic |= (ord(self.maskstring[i]) ^ (cksums[i] & 0x00ff))
      cksum_magic |= (ord(self.maskstring[i + 4]) ^ (cksums[i] >> 8)) << 32
      

    return cksum_magic
 
class PuzzleHeader:
  def read(r):
    hdr = PuzzleHeader()
    hdr.readFrom(r)
    return hdr
  read = Static(read)
  
  format = '''<
               H 11s        xH 
               Q       3s x4s  
               12s         BBH 
               4s'''

  format_hdr = '<BBH4s'
  
  def readFrom(self, r):
    ( self.cksum_gbl, 
      self.acrossDown,
      self.cksum_hdr, 
      self.cksum_magic,
      self.version,
      self.unknown1,
      self.unknown2,
      self.width,
      self.height,
      self.numclues,
      self.flags
    ) = r.unpack(self.format)
    
  def writeTo(self, w):
    w.pack(self.format,
           self.cksum_gbl,
           self.acrossDown,
           self.cksum_hdr, 
           self.cksum_magic,
           self.version,
           self.unknown1,
           self.unknown2,
           self.width,
           self.height,
           self.numclues,
           self.flags
          )

  def validate(self):
    if self.calculateChecksum() != self.cksum_hdr:
      logging.warning('PuzzleHeader: checksum validation failed')
      
    self.validate({
    })
        
  def updateChecksum(self):
    self.cksum_hdr = self.calculateChecksum()
    
  def calculateChecksum(self):
    return cksum_data(struct.pack(self.format_hdr, self.width, self.height, self.numclues, self.flags))

class PuzzleExtension:
  format_hdr = '< 4s  H H '
  format_body = '%dsx'
  format_write = format_hdr + format_body
  
  def read(r):
    record = PuzzleExtension()
    record.readFrom(r)
    return record
  read = Static(read)
  
  def readFrom(self, r):
    (self.code,
     self.length,
     self.cksum
    ) = r.unpack(self.format_hdr)
    
    (self.data,) = r.unpack(self.format_body % self.length)
    
  def writeTo(self, w):
    w.pack(self.format_write % self.length,
           self.code,
           self.length,
           self.cksum,
           self.data)
    
  def getData(self):
    w = PuzzleWriter('ISO-8859-1')
    self.writeTo(w)
    return w.getData()
    
  def validate(self):
    if self.calculateChecksum() != self.cksum:
      logging.warning('PuzzleExtension %s: cksum validation failed' % self.code)
    
  def updateChecksum(self):
    self.cksum = self.calculateChecksum()
      
  def calculateChecksum(self):
    return cksum_data(self.data)
    
class PuzzleReader:
  def __init__(self, data, enc):
    self.data = data
    self.enc = enc
    self.pos = 0
    
  def canRead(self):
    return self.pos < len(self.data)  
    
  def length(self):
    return len(self.data)
  
  def readString(self, count):
    start = self.pos
    self.pos += count
    return self.data[start : self.pos]
  
  def readUnicodeString(self):
    return self.readTo('\0')
    
  def readTo(self, c):
    start = self.pos
    end = self.data.index(c, start)
    self.pos = end + 1
    return unicode(self.data[start:end], self.enc)
    
  def unpack(self, format):
    res = struct.unpack_from(format, self.data, self.pos)
    self.pos += struct.calcsize(format)
    return res
    
class PuzzleWriter:
  def __init__(self, enc):
    self.data = []
    self.enc = enc
    
  def writeString(self, s):
    self.data.append(s)
    
  def writeUnicodeString(self, s):
    self.writeString(s.encode(self.enc) + '\0')
    
  def pack(self, format, *values):
    self.writeString(struct.pack(format, *values))

  def getData(self):
    return ''.join(self.data)

# helper functions for cksums
def cksum_data(data, cksum = 0):
  for c in data:
    b = ord(c)
    # right-shift one with wrap-around
    lowbit = (cksum & 0x0001)
    cksum = (cksum >> 1)
    if lowbit: cksum = (cksum | 0x8000)
    
    # then add in the data and clear any carried bit past 16
    cksum = (cksum + b) & 0xffff
    
  return cksum

