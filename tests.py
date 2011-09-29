import os
import sys
import glob
import unittest
import puz

# this is just a place-holder at this point, need to add real tests
class PuzzleTests(unittest.TestCase):
    def test1(self):
        self.assertEqual(1,1) 
    def test2(self):
        pass

class RoundtripPuzfileTests(unittest.TestCase):
    def __init__(self, filename):
        unittest.TestCase.__init__(self)
        self.filename = filename
        
    def runTest(self):
        try:
            orig = file(self.filename, 'rb').read()
            p = puz.read(self.filename)
            new = p.tostring()
            self.assertEqual(orig, new, '%s did not round-trip' % self.filename)
        except puz.PuzzleFormatError:
            self.assertTrue(False, '%s threw PuzzleFormatError: %s' % (self.filename, sys.exc_info()[1].message))

def tests_in_dir(dir):
    return sum((map(RoundtripPuzfileTests, glob.glob(os.path.join(path, '*.puz')))
                for path, dirs, files in os.walk(dir)), [])

def suite():
    # suite consists of any test* method defined in PuzzleTests, plus a round-trip
    # test for each .puz file in ./testfiles/
    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PuzzleTests))
    suite.addTests(tests_in_dir('testfiles'))
    #suite.addTests(tests_in_dir('../xwordapp/data/'))

    return suite

if __name__ == '__main__':
  print __file__
  unittest.TextTestRunner().run(suite())
