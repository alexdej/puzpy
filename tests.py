import os
import unittest
from puzfile import Puzzle

# this is just a place-holder at this point, need to add real tests
class BasicTest(unittest.TestCase):
  def runTest(self):
   self.assertEqual(1,1) 

class ReadWriteTest(unittest.TestCase):
  def runTest(self):
    for filename in os.listdir('testfiles'):
      if filename.endswith('.puz'):
        try:
          file = open('testfiles' + '/' + filename, 'rb')
          orig = file.read()
          puz = Puzzle.read(orig)
          new = puz.getData()
        except:
          print filename
          raise
        self.assertEqual(orig, new, '%s did not round-trip' % filename)

if __name__ == '__main__':
  unittest.main()
