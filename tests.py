import os
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
    

def test_grid():
    p = puz.read('testfiles/washpost.puz')
    clues = p.clue_numbering()
    a1, d1 = clues.across[0], clues.down[0]
    soln = puz.Grid(p.solution, p.width, p.height)

    # 1-Across (LAMB) and 1-Down (LOFT) both start at index 0 and have length 4
    assert clues.len_across(0) == 4
    assert clues.len_down(0) == 4

    # words that run to the grid edge (no terminating black square)
    edge_across = next(e for e in clues.across if e['col'] + e['len'] == p.width)
    assert clues.len_across(edge_across['cell']) == edge_across['len']
    edge_down = next(e for e in clues.down if e['row'] + e['len'] == p.height)
    assert clues.len_down(edge_down['cell']) == edge_down['len']

    assert 'LAMB' == soln.get_string_for_clue(a1)
    assert 'LOFT' == soln.get_string_for_clue(d1)

    assert soln.get_cell(0, 0) == 'L'
    assert soln.get_column(0)[0] == 'L'
    assert soln.get_string(0, 0, 4) == 'LAMB'
    assert soln.get_string_across(0, 0, 4) == 'LAMB'
    assert soln.get_string_down(0, 0, 4) == 'LOFT'
    assert soln.get_string(0, 0, 4, dir='down') == 'LOFT'

    with pytest.raises(AssertionError):
        soln.get_range(0, 0, 4, dir='diagonal')


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
    assert m
    # this puzzle has 5 circled cells
    assert len(m.get_markup_squares()) == 5
    for i in m.get_markup_squares():
        assert m.is_markup_square(i)
        assert puz.GridMarkup.Circled == m.markup[i]


def test_markup_revealed():
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape_revealed.puz')
    m = p.markup()
    assert m
    # all the cells in this puzzle have been marked Revealed so check that
    for i in m.get_markup_squares():
        assert m.is_markup_square(i)
        assert puz.GridMarkup.Revealed & m.markup[i]
    # also check that at least one of the Circled cells is marked
    assert puz.GridMarkup.Circled & m.markup[7]


def test_no_markup():
    p = puz.read('testfiles/washpost.puz')
    assert not p.has_markup()
    assert not p.markup().has_markup()


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


def test_truncated_puzzle():
    # has the magic string but too short for the full header
    with pytest.raises(puz.PuzzleFormatError):
        puz.load(b'\x00\x00' + puz.ACROSSDOWN + b'\x00' * 5)


def test_checksum_errors():
    with open('testfiles/washpost.puz', 'rb') as fp:
        data = fp.read()

    # header starts 2 bytes before ACROSSDOWN magic string
    base = data.index(puz.ACROSSDOWN) - 2

    # corrupt stored global checksum
    bad = bytearray(data)
    bad[base] ^= 0xFF
    with pytest.raises(puz.PuzzleFormatError, match='global'):
        puz.load(bytes(bad))

    # corrupt stored header checksum — global still passes
    bad = bytearray(data)
    bad[base + 14] ^= 0xFF
    with pytest.raises(puz.PuzzleFormatError, match='header'):
        puz.load(bytes(bad))

    # corrupt stored magic checksum — global and header still pass
    bad = bytearray(data)
    bad[base + 16] ^= 0xFF
    with pytest.raises(puz.PuzzleFormatError, match='magic'):
        puz.load(bytes(bad))


def test_extension_checksum_error():
    data = bytearray(puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz').tobytes())
    pos = data.index(b'GRBS')
    data[pos + 6] ^= 0xFF  # flip a byte in the GRBS extension checksum
    with pytest.raises(puz.PuzzleFormatError, match='extension'):
        puz.load(bytes(data))


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


def test_rebus_player_flow():
    # simulate a player opening a rebus puzzle, entering fill, and saving
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    r = p.rebus()
    assert r.has_rebus()

    assert 3 == len(r.get_rebus_squares())
    for i in r.get_rebus_squares():
        r.set_rebus_fill(i, 'STAR')

    # round-trip and verify fill is preserved
    p2 = puz.load(p.tobytes())
    r2 = p2.rebus()
    for i in r.get_rebus_squares():
        assert r2.get_rebus_fill(i) == 'STAR'


def test_full_construction_roundtrip():
    # build nyt_rebus_with_notes_and_shape.puz from scratch and compare byte-for-byte
    filename = 'testfiles/nyt_rebus_with_notes_and_shape.puz'
    with open(filename, 'rb') as fp:
        orig = fp.read()
    ref = puz.read(filename)

    p = puz.Puzzle()
    p.title = ref.title
    p.author = ref.author
    p.copyright = ref.copyright
    p.notes = ref.notes
    p.width = ref.width
    p.height = ref.height
    p.solution = ref.solution
    p.fill = ref.fill
    p.clues = ref.clues
    # unk fields needed only since we're doing a byte-for-byte comparison
    p.unk1 = ref.unk1
    p.unk2 = ref.unk2

    r = p.rebus()
    r.solutions[1] = 'STAR'
    r.table[22] = r.table[112] = r.table[202] = 2

    m = p.markup()
    m.markup = [0] * (p.width * p.height)
    for i in [7, 47, 56, 168, 177]:
        m.markup[i] = puz.GridMarkup.Circled

    assert orig == p.tobytes()


def test_rebus_constructor_flow():
    # simulate a constructor building a puzzle with a rebus square from scratch
    p = puz.Puzzle()
    p.width = 3
    p.height = 3
    p.solution = 'ABCDEFGHI'
    p.fill = '---------'
    p.clues = ['clue'] * 6

    r = p.rebus()
    r.solutions[0] = 'STAR'
    r.table[4] = 1  # center square, key 0 + 1

    p2 = puz.load(p.tobytes())
    assert p2.rebus().is_rebus_square(4)
    assert p2.rebus().get_rebus_solution(4) == 'STAR'
    assert not p2.rebus().is_rebus_square(0)

    p2.check_answers('ABCDEFGHI')


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


def test_invalid_text_format():
    with pytest.raises(puz.PuzzleFormatError):
        puz.from_text_format('not a valid puzzle')


def test_to_text_format_custom_version():
    p = puz.read('testfiles/washpost.puz')
    text = puz.to_text_format(p, text_version='v2')
    assert text.startswith('<ACROSS PUZZLE v2>')


def test_to_text_format_invalid_version():
    p = puz.read('testfiles/washpost.puz')
    with pytest.raises(ValueError):
        puz.to_text_format(p, text_version=None)


def test_rebus_fill_returns_none_for_non_rebus_square():
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    assert p.rebus().get_rebus_fill(0) is None


@pytest.mark.parametrize('filename', glob.glob('testfiles/*.txt'))
def test_textfile_roundtrip(filename):
    with open(filename, 'r') as fp:
        orig = fp.read()
        p = puz.read_text(filename)
        new = puz.to_text_format(p)
        assert orig == new, '%s did not round-trip' % filename


def test_helpers_roundtrip():
    filename = 'testfiles/nyt_rebus_with_notes_and_shape.puz'
    with open(filename, 'rb') as fp:
        orig = fp.read()
    p = puz.read(filename)
    p.rebus()
    p.markup()
    assert orig == p.tobytes()


def test_nonrebus_helpers_roundtrip():
    filename = 'testfiles/washpost.puz'
    with open(filename, 'rb') as fp:
        orig = fp.read()
    p = puz.read(filename)
    p.has_rebus()   # side effect: instantiates Rebus helper
    p.has_markup()  # side effect: instantiates Markup helper
    assert orig == p.tobytes()


def _not_bad(files):
    return [f for f in files if not f.endswith('_bad.puz')]


@pytest.mark.parametrize('filename', _not_bad(glob.glob('testfiles/*.puz')))
def test_puzfile_roundtrip(filename):
    # test that a .puz file can be read and then written back out without any changes to the bytes
    # purposely doesn't touch markup or rebus to ensure we roundtrip bytes even when the helpers aren't instantiated
    with open(filename, 'rb') as fp:
        orig = fp.read()
        p = puz.read(filename)
        new = p.tobytes()
        assert orig == new, '%s did not round-trip' % filename


@pytest.mark.parametrize('filename', _not_bad(glob.glob('testfiles/*.puz')))
def test_puzfile_roundtrip_with_helpers(filename):
    # variation on the roundtrip test that also instantiates the Rebus and Markup
    # helpers to verify that their save methods roundtrip properly
    with open(filename, 'rb') as fp:
        orig = fp.read()
        p = puz.read(filename)
        p.has_rebus()    # side effect: instantiates Rebus helper
        p.has_markup()   # side effect: instantiates Markup helper
        new = p.tobytes()
        assert orig == new, '%s did not round-trip' % filename


@pytest.mark.parametrize('filename', glob.glob('testfiles/*_bad.puz'))
def test_bad_puzfile_raises_puzzle_format_error(filename):
    with pytest.raises(puz.PuzzleFormatError):
        puz.read(filename)
