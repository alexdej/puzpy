import sys
from puzfile import *

#file = file('puz/cs080904.puz')
#file = file('puz/nytimes/Sep0508.puz')
#file = file('puz/nytimes/Sep1108_thu_withnotes_rebus_shape.puz')
filename = sys.argv[1]

print 'file: %s' % filename

file = open(filename, "rb")


before = file.read(1024*1024)

puzfile = Puzzle.read(before)

print "global checksums: "
print "  file: %x" % puzfile.header.cksum_gbl
print "  calc: %x" % puzfile.calculateGlobalChecksum()
print "magic checksums: "
print "  file: %16x" % puzfile.header.cksum_magic
print "  calc: %16x" % puzfile.calculateMagicChecksum()

answer_cksum = cksum_data(puzfile.answers)
print 'answer_cksum: %02x %02x' % ((answer_cksum & 0x00ff), (answer_cksum >> 8))

print 'unknown1: %s' % (' '.join(['%02x' % ord(c) for c in puzfile.header.unknown1[2:]]))

after = puzfile.getData()

print len(before)
print before
print len(after)
print after


for i in xrange(0, len(after)):
  if before[i] != after[i]:
    print "difference at %i: %c %c" % (i, before[i], after[i])


for ext in puzfile.extensions:
  ext.validate()
