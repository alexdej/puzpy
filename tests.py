import os
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
        except:
            print self.filename
            raise

def suite():
    # suite consists of any test* method defined in PuzzleTests, plus a round-trip
    # test for each .puz file in ./testfiles/
    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PuzzleTests))
    suite.addTests(map(
        RoundtripPuzfileTests, 
        ['testfiles/' + f for f in os.listdir('testfiles') if f.endswith('.puz')]))

    return suite

if __name__ == '__main__':
  print __file__
  unittest.TextTestRunner().run(suite())
