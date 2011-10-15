import os
import sys
import glob
import unittest
import puz

class PuzzleTests(unittest.TestCase):
    def testClueNumbering(self):
        p = puz.read('testfiles/washpost.puz')
        clues = p.clue_numbering()
        self.assertEqual(len(p.clues), len(clues.across) + len(clues.down))
    
    def testExtensions(self):
        p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
        self.assertTrue(puz.Extensions.Rebus in p.extensions)
        self.assertTrue(puz.Extensions.RebusSolutions in p.extensions)
        self.assertTrue(puz.Extensions.Markup in p.extensions)

    def testRebus(self):
        p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
        self.assertTrue(p.has_rebus())
        r = p.rebus()
        self.assertTrue(r.has_rebus())
        self.assertEqual(3, len(r.get_rebus_squares()))
        self.assertTrue(all(r.is_rebus_square(i) for i in r.get_rebus_squares()))
        self.assertTrue(all('STAR' == r.get_rebus_solution(i) for i in r.get_rebus_squares()))
        self.assertTrue(None == r.get_rebus_solution(100))
        # trigger save
        p.tostring()

    def testMarkup(self):
        p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
        self.assertTrue(p.has_markup())
        m = p.markup()
        self.assertTrue(all(puz.GridMarkup.Circled == m.markup[i] for i in m.get_markup_squares()))
        # trigger save
        p.tostring()
        
        p = puz.read('testfiles/washpost.puz')
        self.assertFalse(p.has_markup())
        m = p.markup()
        self.assertFalse(m.has_markup())
        # trigger save
        p.tostring()

    def testPuzzleType(self):
        self.assertFalse(puz.read('testfiles/washpost.puz').puzzletype == puz.PuzzleType.Diagramless)
        self.assertFalse(puz.read('testfiles/nyt_locked.puz').puzzletype == puz.PuzzleType.Diagramless)
        self.assertTrue(puz.read('testfiles/nyt_diagramless.puz').puzzletype == puz.PuzzleType.Diagramless)
                
class LockTests(unittest.TestCase):
    def testScrambleFunctions(self):
        ''' tests some examples from the file format documentation wiki
        '''
        self.assertEqual('MLOOPKJ', puz.scramble_string('AEBFCDG', 1234))
        self.assertEqual('MOP..KLOJ', puz.scramble_solution('ABC..DEFG', 3, 3, 1234))

        self.assertEqual('AEBFCDG', puz.unscramble_string('MLOOPKJ', 1234))
        self.assertEqual('ABC..DEFG', puz.unscramble_solution('MOP..KLOJ', 3, 3, 1234))
        
        # rectangular example - tricky
        a = 'ABCD.EFGH.KHIJKLM.NOPW.XYZ'
        self.assertEqual(a, puz.unscramble_solution(puz.scramble_solution(a, 13, 2, 9721), 13, 2, 9721))
        
    def testLockedBit(self):
        self.assertFalse(puz.read('testfiles/washpost.puz').is_solution_locked())
        self.assertTrue(puz.read('testfiles/nyt_locked.puz').is_solution_locked())

    def testUnlock(self):
        p = puz.read('testfiles/nyt_locked.puz')
        self.assertTrue(p.is_solution_locked())
        self.assertFalse(p.unlock_solution(1234))
        self.assertTrue(p.is_solution_locked()) # still locked
        self.assertTrue(p.unlock_solution(7844))
        self.assertFalse(p.is_solution_locked()) # unlocked!
        self.assertTrue('LAKEONTARIO' in p.solution)

    def testUnlockRelock(self):
        orig = file('testfiles/nyt_locked.puz', 'rb').read()
        p = puz.read('testfiles/nyt_locked.puz')
        self.assertTrue(p.is_solution_locked())
        self.assertTrue(p.unlock_solution(7844))
        p.lock_solution(7844)
        new = p.tostring()
        self.assertEqual(orig, new, 'nyt_locked.puz dit not found-trip')
        
    def testCheckAnswersLocked(self):
        '''Verify that we can check answers even when the solution is locked
        '''
        p1 = puz.read('testfiles/nyt_locked.puz')
        p2 = puz.read('testfiles/nyt_locked.puz')
        p1.unlock_solution(7844)
        self.assertTrue(p2.is_solution_locked())
        self.assertTrue(p2.check_answers(p1.solution))

class RoundtripPuzfileTests(unittest.TestCase):
    def __init__(self, filename):
        unittest.TestCase.__init__(self)
        self.filename = filename
        
    def runTest(self):
        try:
            orig = file(self.filename, 'rb').read()
            p = puz.read(self.filename)
            if (p.puzzletype == puz.PuzzleType.Normal):
                clues = p.clue_numbering()
                # smoke test the clue numbering while we're at it
                self.assertEqual(len(p.clues), len(clues.across) + len(clues.down), 'failed in %s' % self.filename)
            # this is the roundtrip
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
    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(LockTests))
    suite.addTests(tests_in_dir('testfiles'))
    #suite.addTests(tests_in_dir('../xwordapp/data/'))

    return suite

if __name__ == '__main__':
  print __file__
  unittest.TextTestRunner().run(suite())
