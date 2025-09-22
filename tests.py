import os
import sys
import tempfile
import pytest
import glob

import puz


def temp_filename(suffix='puz'):
    # uses NamedTemporaryFile to create a temporary file but then exits the context
    # so as to close the fd and unlink the file. These tests typically want a filename
    # they can write to which doesn't work on every OS when the fd is open.
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        return tmp.name


def test_clue_numbering():
    p = puz.read('testfiles/washpost.puz')
    clues = p.clue_numbering()
    assert len(p.clues) == len(clues.across) + len(clues.down)
    assert len(p.clues) > 0

    a1 = clues.across[0]
    assert a1['num'] == 1
    assert a1['dir'] == 'across'
    assert a1['clue'] == "Mary's pet"
    assert a1['clue_index'] == 0
    assert a1['cell'] == 0
    assert a1['row'] == 0
    assert a1['col'] == 0
    assert a1['len'] == 4

    assert a1['clue'] == p.clues[a1['clue_index']]

    d1 = clues.down[0]
    assert d1['num'] == 1
    assert d1['dir'] == 'down'
    assert d1['clue'] == "Hit high in the air"
    assert d1['clue_index'] == 1
    assert d1['cell'] == 0
    assert d1['row'] == 0
    assert d1['col'] == 0
    assert d1['len'] == 4

    assert d1['clue'] == p.clues[d1['clue_index']]

    soln = puz.Grid(p.solution, p.width, p.height)
    assert 'LAMB' == soln.get_string_for_clue(a1)
    assert 'LOFT' == soln.get_string_for_clue(d1)


def test_diagramless_clue_numbering():
    p = puz.read('testfiles/nyt_diagramless.puz')
    clues = p.clue_numbering()
    assert len(p.clues) == len(clues.across) + len(clues.down)
    assert len(p.clues) > 0


def test_extensions():
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    assert puz.Extensions.Rebus in p.extensions
    assert puz.Extensions.RebusSolutions in p.extensions
    assert puz.Extensions.Markup in p.extensions


def test_rebus():
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    assert p.has_rebus()
    r = p.rebus()
    assert r.has_rebus()
    assert 3 == len(r.get_rebus_squares())
    for i in r.get_rebus_squares():
        assert r.is_rebus_square(i)
        assert 'STAR' == r.get_rebus_solution(i)
    assert r.get_rebus_solution(100) is None


def test_markup():
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    assert p.has_markup()
    m = p.markup()
    for i in m.get_markup_squares():
        assert puz.GridMarkup.Circled == m.markup[i] and m.is_markup_square(i)

    p = puz.read('testfiles/washpost.puz')
    assert not p.has_markup()
    m = p.markup()
    assert not m.has_markup()


def test_puzzle_type():
    assert puz.read('testfiles/washpost.puz').puzzletype == puz.PuzzleType.Normal
    assert puz.read('testfiles/nyt_locked.puz').puzzletype == puz.PuzzleType.Normal
    assert puz.read('testfiles/nyt_diagramless.puz').puzzletype == puz.PuzzleType.Diagramless


def test_empty_puzzle():
    p = puz.Puzzle()
    with pytest.raises(puz.PuzzleFormatError):
        p.load(b'')


def test_corrupted_puzzle():
    p = puz.Puzzle()
    with pytest.raises(puz.PuzzleFormatError):
        p.load(b'not a puzzle')


def test_junk_at_end_of_puzzle():
    with open('testfiles/washpost.puz', 'rb') as fp:
        data = fp.read() + b'\r\n\r\n'
    p = puz.Puzzle()
    p.load(data)
    assert p.postscript == b'\r\n\r\n'


def test_v1_4():
    p = puz.read('testfiles/nyt_v1_4.puz')
    assert p.version_tuple() == (1, 4)


def test_v2_unicode():
    p = puz.read('testfiles/unicode.puz')
    assert p.title == u'\u2694\ufe0f'
    assert p.encoding == 'UTF-8'
    assert p.version_tuple() == (2, 0)


def test_v2_upgrade():
    p = puz.read('testfiles/washpost.puz')
    p.title = u'\u2694\ufe0f'
    p.set_version('2.0')
    p.encoding = puz.ENCODING_UTF8
    data = p.tobytes()
    p2 = puz.load(data)
    assert p2.title == u'\u2694\ufe0f'
    assert p2.version_tuple() == (2, 0)


def test_save_empty_puzzle():
    filename = temp_filename()
    try:
        p = puz.Puzzle()
        p.save(filename)
        p2 = puz.read(filename)
        assert p.puzzletype == p2.puzzletype
        assert p.version == p2.version
        assert p.scrambled_cksum == p2.scrambled_cksum
    finally:
        os.unlink(filename)


def test_save_small_puzzle():
    filename = temp_filename()
    try:
        p = puz.Puzzle()
        p.title = 'Test Puzzle'
        p.author = 'Alex'
        p.height = 3
        p.width = 3
        p.solution = 'A' * 9
        p.clues = ['clue'] * 6
        p.fill = '-' * 9
        p.save(filename)
        p2 = puz.read(filename)
        assert p.title == p2.title
        assert p.author == p2.author
        assert p.solution == p2.solution
        assert p.clues == p2.clues
        assert p.fill == p2.fill
    finally:
        os.unlink(filename)


def test_scramble_functions():
    assert 'MLOOPKJ' == puz.scramble_string('AEBFCDG', 1234)
    assert 'MOP..KLOJ' == puz.scramble_solution('ABC..DEFG', 3, 3, 1234)
    assert 'AEBFCDG' == puz.unscramble_string('MLOOPKJ', 1234)
    assert 'ABC..DEFG' == puz.unscramble_solution('MOP..KLOJ', 3, 3, 1234)
    a = 'ABCD.EFGH.KHIJKLM.NOPW.XYZ'
    scrambled = puz.scramble_solution(a, 13, 2, 9721)
    unscrambled = puz.unscramble_solution(scrambled, 13, 2, 9721)
    assert a == unscrambled


def test_locked_bit():
    assert not puz.read('testfiles/washpost.puz').is_solution_locked()
    assert puz.read('testfiles/nyt_locked.puz').is_solution_locked()


def test_unlock():
    p = puz.read('testfiles/nyt_locked.puz')
    assert p.is_solution_locked()
    assert not p.unlock_solution(1234)
    assert p.is_solution_locked()
    assert p.unlock_solution(7844)
    assert not p.is_solution_locked()
    assert 'LAKEONTARIO' in p.solution


def test_unlock_relock():
    with open('testfiles/nyt_locked.puz', 'rb') as fp:
        orig = fp.read()
    p = puz.read('testfiles/nyt_locked.puz')
    assert p.is_solution_locked()
    assert p.unlock_solution(7844)
    p.lock_solution(7844)
    new = p.tobytes()
    assert orig == new, 'nyt_locked.puz did not round-trip'


def test_check_answers_locked():
    p1 = puz.read('testfiles/nyt_locked.puz')
    p2 = puz.read('testfiles/nyt_locked.puz')
    p1.unlock_solution(7844)
    assert p2.is_solution_locked()
    assert p2.check_answers(p1.solution)


def test_unlock_relock_diagramless():
    with open('testfiles/nyt_diagramless.puz', 'rb') as fp:
        orig = fp.read()
    p = puz.read('testfiles/nyt_diagramless.puz')
    assert p.is_solution_locked()
    assert p.unlock_solution(3285)
    assert not p.is_solution_locked()
    p.lock_solution(3285)
    new = p.tobytes()
    assert orig == new, 'nyt_diagramless.puz did not round-trip'


def test_text_format():
    p = puz.read_text('testfiles/text_format_v1.txt')
    assert p.title == 'Politics: Who, what, where and why'
    assert p.author == 'Created by Avalonian'
    assert p.copyright == '1995 Literate Software Systems'
    assert p.width == 15
    assert p.height == 15
    assert p.fill.startswith('----.-----.----')
    assert p.solution.startswith('FATE.AWASH.AWOL')
    assert len(p.clues) == 78
    assert p.notes == 'This is an example notepad entry with\ntwo lines in it.'

    assert not p.is_solution_locked()
    numbering = p.clue_numbering()
    assert len(numbering.across) == 39
    assert numbering.across[0]['num'] == 1
    assert numbering.across[0]['clue'] == 'Destiny'
    assert numbering.across[-1]['num'] == 61
    assert numbering.across[-1]['clue'] == 'Encourage'
    assert len(numbering.down) == 39
    assert numbering.down[0]['num'] == 1
    assert numbering.down[0]['clue'] == 'Biting insect'
    assert numbering.down[-1]['num'] == 55
    assert numbering.down[-1]['clue'] == 'Tax break savings account'
    

def test_convert_text_to_puz():
    p = puz.read_text('testfiles/text_format_v1.txt')
    bytes = p.tobytes()
    p2 = puz.load(bytes)
    assert p.title == p2.title
    assert p.author == p2.author
    assert p.copyright == p2.copyright
    assert p.width == p2.width
    assert p.height == p2.height
    assert p.fill == p2.fill
    assert p.solution == p2.solution
    assert p.clues == p2.clues
    assert p.notes == p2.notes
    numbering = p.clue_numbering()
    assert len(numbering.across) == len(p2.clue_numbering().across)
    assert len(numbering.down) == len(p2.clue_numbering().down)


def test_convert_puz_to_text():
    p = puz.read('testfiles/washpost.puz')
    text = puz.to_text_format(p)
    p2 = puz.load_text(text)
    assert p.title == p2.title
    assert p.author == p2.author
    assert p.copyright == p2.copyright
    assert p.width == p2.width
    assert p.height == p2.height
    assert p.fill == p2.fill
    assert p.solution == p2.solution
    assert p.clues == p2.clues
    assert p.notes == p2.notes
    numbering = p.clue_numbering()
    assert len(numbering.across) == len(p2.clue_numbering().across)
    assert len(numbering.down) == len(p2.clue_numbering().down)


@pytest.mark.parametrize('filename', glob.glob('testfiles/*.txt'))
def test_textfile_roundtrip(filename):
    with open(filename, 'r') as fp:
        orig = fp.read()
        p = puz.read_text(filename)
        new = puz.to_text_format(p)
        assert orig == new, '%s did not round-trip' % filename


@pytest.mark.parametrize('filename', glob.glob('testfiles/*.puz'))
def test_puzfile_roundtrip(filename):
    is_bad = filename.endswith('_bad.puz')
    if is_bad:
        with pytest.raises(puz.PuzzleFormatError):
            puz.read(filename)
    else:
        with open(filename, 'rb') as fp:
            orig = fp.read()
            p = puz.read(filename)
            new = p.tobytes()
            assert orig == new, '%s did not round-trip' % filename


def test_update_readme_test():
    # update the test_readme.py file if README.md has changed
    from pytest_readme import setup
    setup()


if __name__ == '__main__':
    print(__file__)
    result = pytest.main()
    sys.exit(result)
