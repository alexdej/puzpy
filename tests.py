import glob
import os
import sys
import unittest

import puz


class PuzzleTests(unittest.TestCase):

    def test_clue_numbering(self):
        p = puz.read('testfiles/washpost.puz')
        clues = p.clue_numbering()
        self.assertEqual(len(p.clues), len(clues.across) + len(clues.down))

    def test_extensions(self):
        p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
        self.assertIn(puz.Extensions.Rebus, p.extensions)
        self.assertIn(puz.Extensions.RebusSolutions, p.extensions)
        self.assertIn(puz.Extensions.Markup, p.extensions)

    def test_rebus(self):
        p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
        self.assertTrue(p.has_rebus())
        r = p.rebus()
        self.assertTrue(r.has_rebus())
        self.assertEqual(3, len(r.get_rebus_squares()))
        self.assertTrue(all(r.is_rebus_square(i)
                            for i in r.get_rebus_squares()))
        self.assertTrue(all('STAR' == r.get_rebus_solution(i)
                            for i in r.get_rebus_squares()))
        self.assertEqual(None, r.get_rebus_solution(100))
        # trigger save
        p.tobytes()

    def test_markup(self):
        p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
        self.assertTrue(p.has_markup())
        m = p.markup()
        self.assertTrue(all(puz.GridMarkup.Circled == m.markup[i]
                            for i in m.get_markup_squares()))
        # trigger save
        p.tobytes()

        p = puz.read('testfiles/washpost.puz')
        self.assertFalse(p.has_markup())
        m = p.markup()
        self.assertFalse(m.has_markup())
        # trigger save
        p.tobytes()

    def test_puzzle_type(self):
        self.assertNotEqual(
            puz.read('testfiles/washpost.puz').puzzletype,
            puz.PuzzleType.Diagramless)
        self.assertNotEqual(
            puz.read('testfiles/nyt_locked.puz').puzzletype,
            puz.PuzzleType.Diagramless)
        self.assertEqual(
            puz.read('testfiles/nyt_diagramless.puz').puzzletype,
            puz.PuzzleType.Diagramless)

    def test_empty_puzzle(self):
        p = puz.Puzzle()
        with self.assertRaises(puz.PuzzleFormatError):
            p.load(b'')

    def test_junk_at_end_of_puzzle(self):
        with open('testfiles/washpost.puz', 'rb') as fp:
            data = fp.read() + b'\r\n\r\n'
        p = puz.Puzzle()
        p.load(data)
        self.assertEqual(p.postscript, b'\r\n\r\n')


class LockTests(unittest.TestCase):

    def test_scramble_functions(self):
        ''' tests some examples from the file format documentation wiki
        '''
        self.assertEqual('MLOOPKJ', puz.scramble_string('AEBFCDG', 1234))
        self.assertEqual('MOP..KLOJ',
                         puz.scramble_solution('ABC..DEFG', 3, 3, 1234))

        self.assertEqual('AEBFCDG', puz.unscramble_string('MLOOPKJ', 1234))
        self.assertEqual('ABC..DEFG',
                         puz.unscramble_solution('MOP..KLOJ', 3, 3, 1234))

        # rectangular example - tricky
        a = 'ABCD.EFGH.KHIJKLM.NOPW.XYZ'
        scrambled = puz.scramble_solution(a, 13, 2, 9721)
        unscrambled = puz.unscramble_solution(scrambled, 13, 2, 9721)
        self.assertEqual(a, unscrambled)

    def test_locked_bit(self):
        self.assertFalse(
            puz.read('testfiles/washpost.puz').is_solution_locked())
        self.assertTrue(
            puz.read('testfiles/nyt_locked.puz').is_solution_locked())

    def test_unlock(self):
        p = puz.read('testfiles/nyt_locked.puz')
        self.assertTrue(p.is_solution_locked())
        self.assertFalse(p.unlock_solution(1234))
        self.assertTrue(p.is_solution_locked())  # still locked
        self.assertTrue(p.unlock_solution(7844))
        self.assertFalse(p.is_solution_locked())  # unlocked!
        self.assertIn('LAKEONTARIO', p.solution)

    def test_unlock_relock(self):
        with open('testfiles/nyt_locked.puz', 'rb') as fp:
            orig = fp.read()
        p = puz.read('testfiles/nyt_locked.puz')
        self.assertTrue(p.is_solution_locked())
        self.assertTrue(p.unlock_solution(7844))
        p.lock_solution(7844)
        new = p.tobytes()
        self.assertEqual(orig, new, 'nyt_locked.puz did not round-trip')

    def test_check_answers_locked(self):
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
            with open(self.filename, 'rb') as fp_filename:
                orig = fp_filename.read()
                p = puz.read(self.filename)
                if (p.puzzletype == puz.PuzzleType.Normal):
                    clues = p.clue_numbering()
                    # smoke test the clue numbering while we're at it
                    self.assertEqual(
                        len(p.clues), len(clues.across) + len(clues.down),
                        'failed in %s' % self.filename)
                # this is the roundtrip
                new = p.tobytes()
                self.assertEqual(orig, new,
                                 '%s did not round-trip' % self.filename)
        except puz.PuzzleFormatError:
            args = (self.filename, sys.exc_info()[1].message)
            self.assertTrue(False, '%s threw PuzzleFormatError: %s' % args)


def tests_in_dir(directory):
    tests = []
    for path, _, _ in os.walk(directory):
        for filename in glob.glob(os.path.join(path, '*.puz')):
            tests.append(RoundtripPuzfileTests(filename))
    return tests


def suite():
    # suite consists of any test* method defined in PuzzleTests,
    # plus a round-trip test for each .puz file in ./testfiles/
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    suite.addTests(loader.loadTestsFromTestCase(PuzzleTests))
    suite.addTests(loader.loadTestsFromTestCase(LockTests))
    suite.addTests(tests_in_dir('testfiles'))
    return suite


if __name__ == '__main__':
    print(__file__)
    unittest.TextTestRunner().run(suite())
