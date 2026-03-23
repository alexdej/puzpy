import os
import sys
import tempfile
import pytest
import glob

import puz
import puz_viewer


def temp_filename(suffix: str = 'puz') -> str:
    # uses NamedTemporaryFile to create a temporary file but then exits the context
    # so as to close the fd and unlink the file. These tests typically want a filename
    # they can write to which doesn't work on every OS when the fd is open.
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        return tmp.name


def test_clue_numbering() -> None:
    p = puz.read('testfiles/washpost.puz')
    clues = p.clue_numbering()
    assert len(p.clues) == len(clues.across) + len(clues.down)
    assert len(p.clues) > 0

    # clue_numbering() returns a ClueNumbering (which is still a DefaultClueNumbering)
    assert isinstance(clues, puz.ClueNumbering)
    assert isinstance(clues, puz.DefaultClueNumbering)

    a1 = clues.across[0]

    # legacy dict access still works
    assert a1['num'] == 1
    assert a1['dir'] == 'across'
    assert a1['clue'] == "Mary's pet"
    assert a1['clue_index'] == 0
    assert a1['cell'] == 0
    assert a1['row'] == 0
    assert a1['col'] == 0
    assert a1['len'] == 4
    assert a1['clue'] == p.clues[a1['clue_index']]

    # ClueEntry is a dict
    assert isinstance(a1, dict)

    # clean property access
    assert a1.number == 1
    assert a1.direction == 'across'
    assert a1.text == "Mary's pet"
    assert a1.cell == 0
    assert a1.row == 0
    assert a1.col == 0
    assert a1.length == 4

    # fill() and solution() return the answer string for this clue
    assert a1.solution == 'LAMB'
    assert len(a1.fill) == a1.length

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

    assert d1.number == 1
    assert d1.direction == 'down'
    assert d1.text == "Hit high in the air"
    assert d1.solution == 'LOFT'


def test_grid() -> None:
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

    # rows() yields each row as a list of cells
    rows = list(soln.rows())
    assert len(rows) == p.height
    assert rows[0] == soln.get_row(0)
    assert rows[-1] == soln.get_row(p.height - 1)

    # cols() yields each column as a list of cells
    cols = list(soln.cols())
    assert len(cols) == p.width
    assert cols[0] == soln.get_column(0)
    assert cols[-1] == soln.get_column(p.width - 1)

    # iterating a Grid is equivalent to rows()
    assert list(soln) == rows

    # factory methods on Puzzle
    fill_grid = p.grid()
    assert isinstance(fill_grid, puz.Grid)
    assert fill_grid.grid == p.fill
    assert fill_grid.width == p.width
    assert fill_grid.height == p.height

    sol_grid = p.solution_grid()
    assert isinstance(sol_grid, puz.Grid)
    assert sol_grid.grid == p.solution


def test_diagramless_clue_numbering() -> None:
    p = puz.read('testfiles/nyt_diagramless.puz')
    clues = p.clue_numbering()
    assert len(p.clues) == len(clues.across) + len(clues.down)
    assert len(p.clues) > 0


def test_is_blacksquare() -> None:
    assert puz.is_blacksquare('.')
    assert puz.is_blacksquare(':')
    assert not puz.is_blacksquare('#')
    assert not puz.is_blacksquare('-')
    assert not puz.is_blacksquare(' ')
    assert not puz.is_blacksquare('')
    assert not puz.is_blacksquare('A')
    assert not puz.is_blacksquare(0)
    assert not puz.is_blacksquare(None)  # type: ignore

    assert puz.is_blacksquare(ord('.'))
    assert puz.is_blacksquare(ord(':'))
    assert not puz.is_blacksquare(ord('#'))
    assert not puz.is_blacksquare(ord('A'))


def test_extensions() -> None:
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    assert puz.Extensions.Rebus in p.extensions
    assert puz.Extensions.RebusSolutions in p.extensions
    assert puz.Extensions.Markup in p.extensions


def test_rebus() -> None:
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    assert p.has_rebus()
    r = p.rebus()
    assert r.has_rebus()
    assert 3 == len(r.get_rebus_squares())
    for i in r.get_rebus_squares():
        assert r.is_rebus_square(i)
        assert 'STAR' == r.get_rebus_solution(i)

    i = r.get_rebus_squares()[0]
    r.set_rebus_fill(i, 'STAR')
    assert r.check_rebus_fill(i)
    assert not r.check_rebus_fill(r.get_rebus_squares())
    assert not r.check_rebus_fill()
    assert r.check_rebus_fill(strict=False)

    assert not p.check_rebus_answers()  # strict=True
    assert p.check_rebus_answers(strict=False)

    for i in r.get_rebus_squares():
        r.set_rebus_fill(i, 'STAR')
    assert r.check_rebus_fill()
    assert p.check_rebus_answers()

    i = r.get_rebus_squares()[-1]
    r.set_rebus_fill(i, 'HEART')
    assert not r.check_rebus_fill(i)
    assert not r.check_rebus_fill()
    assert not p.check_rebus_answers()  # strict=True

    assert r.get_rebus_solution(100) is None


def test_markup() -> None:
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    assert p.has_markup()
    m = p.markup()
    assert m
    # this puzzle has 5 circled cells
    assert len(m.get_markup_squares()) == 5
    for i in m.get_markup_squares():
        assert m.is_markup_square(i)
        assert m.is_markup_square(i, [puz.GridMarkup.Circled])
        assert not m.is_markup_square(i, [puz.GridMarkup.Revealed])
        assert puz.GridMarkup.Circled == m.markup[i]


def test_markup_revealed() -> None:
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape_revealed.puz')
    m = p.markup()
    assert m
    assert m.has_markup()
    assert m.has_markup([puz.GridMarkup.Revealed])
    assert m.has_markup([puz.GridMarkup.Circled])
    assert m.has_markup([puz.GridMarkup.Revealed, puz.GridMarkup.Incorrect])  # should be an OR, not an AND
    assert not m.has_markup([puz.GridMarkup.Incorrect])

    # all the cells in this puzzle have been marked Revealed so check that
    for i in m.get_markup_squares([puz.GridMarkup.Revealed]):
        assert m.is_markup_square(i, [puz.GridMarkup.Revealed])
        assert m.is_markup_square(i)
        assert not m.is_markup_square(i, [puz.GridMarkup.Incorrect])

    # also check that at least one of the Circled cells is marked
    assert m.is_markup_square(7, [puz.GridMarkup.Circled])

    assert not m.get_markup_squares([puz.GridMarkup.Incorrect])


def test_no_markup() -> None:
    p = puz.read('testfiles/washpost.puz')
    assert not p.has_markup()
    assert not p.markup().has_markup()


def test_no_rebus() -> None:
    p = puz.read('testfiles/washpost.puz')
    assert not p.has_rebus()
    assert p.check_rebus_answers()  # should return True since no rebus squares to check


def test_repr() -> None:
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    assert repr(p).startswith('Puzzle(')
    assert repr(p.rebus()).startswith('Rebus(')
    assert repr(p.markup()).startswith('Markup(')
    assert repr(p.clue_numbering()).startswith('ClueNumbering(')
    assert repr(puz.Grid(p.solution, p.width, p.height)).startswith('Grid(')
    assert repr(puz.PuzzleBuffer(b'test')).startswith('PuzzleBuffer(')
    p2 = puz.read('testfiles/nyt_partlyfilled.puz')
    assert repr(p2.timer()).startswith('Timer(')


def test_puzzle_type() -> None:
    assert puz.read('testfiles/washpost.puz').puzzletype == puz.PuzzleType.Normal
    assert puz.read('testfiles/nyt_locked.puz').puzzletype == puz.PuzzleType.Normal
    assert puz.read('testfiles/nyt_diagramless.puz').puzzletype == puz.PuzzleType.Diagramless


def test_empty_puzzle() -> None:
    p = puz.Puzzle()
    with pytest.raises(puz.PuzzleFormatError):
        p.load(b'')


def test_corrupted_puzzle() -> None:
    p = puz.Puzzle()
    with pytest.raises(puz.PuzzleFormatError):
        p.load(b'not a puzzle')


def test_truncated_puzzle() -> None:
    # has the magic string but too short for the full header
    with pytest.raises(puz.PuzzleFormatError):
        puz.load(b'\x00\x00' + puz.ACROSSDOWN + b'\x00' * 5)


def test_checksum_errors() -> None:
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


def test_extension_checksum_error() -> None:
    data = bytearray(puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz').tobytes())
    pos = data.index(b'GRBS')
    data[pos + 6] ^= 0xFF  # flip a byte in the GRBS extension checksum
    with pytest.raises(puz.PuzzleFormatError, match='extension'):
        puz.load(bytes(data))


def test_junk_at_end_of_puzzle() -> None:
    with open('testfiles/washpost.puz', 'rb') as fp:
        data = fp.read() + b'\r\n\r\n'
    p = puz.Puzzle()
    p.load(data)
    assert p.postscript == b'\r\n\r\n'


def test_v1_4() -> None:
    p = puz.read('testfiles/nyt_v1_4.puz')
    assert p.version_tuple() == (1, 4)


def test_v2_unicode() -> None:
    p = puz.read('testfiles/unicode.puz')
    assert p.title == u'\u2694\ufe0f'
    assert p.encoding == 'UTF-8'
    assert p.version_tuple() == (2, 0)


def test_v2_upgrade() -> None:
    p = puz.read('testfiles/washpost.puz')
    p.title = u'\u2694\ufe0f'
    p.set_version('2.0')
    p.encoding = puz.ENCODING_UTF8
    data = p.tobytes()
    p2 = puz.load(data)
    assert p2.title == u'\u2694\ufe0f'
    assert p2.version_tuple() == (2, 0)


def test_save_empty_puzzle() -> None:
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


def test_save_small_puzzle() -> None:
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


def test_rebus_fill_parsing() -> None:
    # nyt_rebus_with_notes_and_shape_solved.puz has RebusFill data with all three
    # rebus squares filled with 'STAR'
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape_solved.puz')
    r = p.rebus()
    assert r.has_rebus()
    for i in r.get_rebus_squares():
        assert r.get_rebus_fill(i) == 'STAR'
    # non-rebus squares have no fill
    assert r.get_rebus_fill(0) is None


def test_rebus_player_flow() -> None:
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


def test_full_construction_roundtrip() -> None:
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
    m.set_markup_squares([7, 47, 56, 168, 177], puz.GridMarkup.Circled)

    assert orig == p.tobytes()


def test_rebus_constructor_flow() -> None:
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


def test_scramble_functions() -> None:
    assert 'MLOOPKJ' == puz.scramble_string('AEBFCDG', 1234)
    assert 'MOP..KLOJ' == puz.scramble_solution('ABC..DEFG', 3, 3, 1234)
    assert 'AEBFCDG' == puz.unscramble_string('MLOOPKJ', 1234)
    assert 'ABC..DEFG' == puz.unscramble_solution('MOP..KLOJ', 3, 3, 1234)
    a = 'ABCD.EFGH.KHIJKLM.NOPW.XYZ'
    scrambled = puz.scramble_solution(a, 13, 2, 9721)
    unscrambled = puz.unscramble_solution(scrambled, 13, 2, 9721)
    assert a == unscrambled


def test_locked_bit() -> None:
    assert not puz.read('testfiles/washpost.puz').is_solution_locked()
    assert puz.read('testfiles/nyt_locked.puz').is_solution_locked()


def test_unlock() -> None:
    p = puz.read('testfiles/nyt_locked.puz')
    assert p.is_solution_locked()
    assert not p.unlock_solution(1234)
    assert p.is_solution_locked()
    assert p.unlock_solution(7844)
    assert not p.is_solution_locked()
    assert 'LAKEONTARIO' in p.solution


def test_unlock_relock() -> None:
    with open('testfiles/nyt_locked.puz', 'rb') as fp:
        orig = fp.read()
    p = puz.read('testfiles/nyt_locked.puz')
    assert p.is_solution_locked()
    assert p.unlock_solution(7844)
    p.lock_solution(7844)
    new = p.tobytes()
    assert orig == new, 'nyt_locked.puz did not round-trip'


def test_check_answers_locked() -> None:
    p1 = puz.read('testfiles/nyt_locked.puz')
    p2 = puz.read('testfiles/nyt_locked.puz')
    p1.unlock_solution(7844)
    assert p2.is_solution_locked()
    assert p2.check_answers(p1.solution)


def test_check_answers_strict() -> None:
    p = _make_puzzle()  # solution = 'ABCDEFGHI', fill = '---------'
    partial_fill = 'ABC------'   # first row correct, rest blank
    wrong_fill = 'ABCDEFGHX'  # one cell wrong

    # strict=True (default): unfilled cells count as wrong
    assert not p.check_answers(partial_fill)
    assert not p.check_answers(wrong_fill)

    # strict=False: unfilled cells are skipped, only wrong filled cells fail
    assert p.check_answers(partial_fill, strict=False)
    assert not p.check_answers(wrong_fill, strict=False)

    # strict=False raises on a locked puzzle
    p_locked = puz.read('testfiles/nyt_locked.puz')
    with pytest.raises(ValueError):
        p_locked.check_answers(p_locked.fill, strict=False)


def test_unlock_relock_diagramless() -> None:
    with open('testfiles/nyt_diagramless.puz', 'rb') as fp:
        orig = fp.read()
    p = puz.read('testfiles/nyt_diagramless.puz')
    assert p.is_solution_locked()
    assert p.unlock_solution(3285)
    assert not p.is_solution_locked()
    p.lock_solution(3285)
    new = p.tobytes()
    assert orig == new, 'nyt_diagramless.puz did not round-trip'


def test_text_format() -> None:
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


def test_text_format_diagramless() -> None:
    # Grid:  AB:CD / EFGHI / :JKLM / NOPQR / STUVW
    # ':' is the diagramless black square character
    text = '\n'.join([
        '<ACROSS PUZZLE>',
        '<TITLE>', '\tDiagramless Test',
        '<AUTHOR>', '\tTest Author',
        '<COPYRIGHT>', '',
        '<SIZE>', '\t5x5',
        '<GRID>',
        '\tAB:CD',
        '\tEFGHI',
        '\t:JKLM',
        '\tNOPQR',
        '\tSTUVW',
        '<ACROSS>',
        '\tclue 1', '\tclue 2', '\tclue 3', '\tclue 4', '\tclue 5', '\tclue 6',
        '<DOWN>',
        '\tclue 7', '\tclue 8', '\tclue 9', '\tclue 10', '\tclue 11', '\tclue 12',
    ])
    p = puz.from_text_format(text)
    assert p.puzzletype == puz.PuzzleType.Diagramless
    assert p.solution == 'AB:CDEFGHI:JKLMNOPQRSTUVW'
    # fill must use ':' (not '-') for black squares so clue_numbering works
    assert p.fill == '--:-------:--------------'
    numbering = p.clue_numbering()
    assert len(numbering.across) + len(numbering.down) == len(p.clues)


def test_text_format_rebus() -> None:
    p = puz.read_text('testfiles/text_format_v2_rebus.txt')
    assert p.width == 5
    assert p.height == 5
    r = p.rebus()
    assert r.has_rebus()
    assert r.is_rebus_square(0)
    assert r.get_rebus_solution(0) == 'STAR'
    assert p.solution[0] == 'S'   # short char stored in solution
    assert r.is_rebus_square(5)
    assert r.get_rebus_solution(5) == 'BIG'
    assert p.solution[5] == 'B'
    assert not r.is_rebus_square(1)


def test_text_format_rebus_shared_solution() -> None:
    # two cells with the same rebus solution should share one key in solutions
    text = '\n'.join([
        '<ACROSS PUZZLE v2>',
        '<TITLE>', '\t',
        '<AUTHOR>', '\t',
        '<COPYRIGHT>', '\t',
        '<SIZE>', '\t3x3',
        '<GRID>', '\t1B1', '\tDEF', '\tGHI',
        '<REBUS>', '\t1:STAR:S',
        '<ACROSS>', '\tclue', '\tclue', '\tclue',
        '<DOWN>', '\tclue', '\tclue', '\tclue',
        '<NOTEPAD>', '',
    ])
    p = puz.from_text_format(text)
    r = p.rebus()
    assert r.is_rebus_square(0)
    assert r.is_rebus_square(2)
    assert r.get_rebus_solution(0) == 'STAR'
    assert r.get_rebus_solution(2) == 'STAR'
    assert len(r.solutions) == 1  # shared, not duplicated


def test_text_format_rebus_mark_flag() -> None:
    # MARK flag: lowercase letters in grid are treated as circled cells
    # also tests blank lines in the REBUS section (which should be skipped)
    text = '\n'.join([
        '<ACROSS PUZZLE v2>',
        '<TITLE>', '\tMARK Test',
        '<AUTHOR>', '\t',
        '<COPYRIGHT>', '\t',
        '<SIZE>', '\t3x3',
        '<GRID>', '\taBc', '\tDEF', '\tGHI',
        '<REBUS>',
        '',          # blank line — should be silently skipped
        '\tMARK;',   # MARK flag
        '<ACROSS>', '\tclue', '\tclue', '\tclue',
        '<DOWN>', '\tclue', '\tclue', '\tclue',
        '<NOTEPAD>', '',
    ])
    p = puz.from_text_format(text)
    assert p.solution == 'ABCDEFGHI'   # lowercase letters uppercased
    assert not p.rebus().has_rebus()   # MARK flag alone doesn't create rebus squares
    m = p.markup()
    assert m.is_markup_square(0, [puz.GridMarkup.Circled])
    assert not m.is_markup_square(1, [puz.GridMarkup.Circled])  # 'B' — uppercase, not circled
    assert m.is_markup_square(2, [puz.GridMarkup.Circled])


def test_text_format_mark_write() -> None:
    p = puz.read_text('testfiles/text_format_v2_mark.txt')
    # verify circles were read correctly
    m = p.markup()
    assert m.is_markup_square(0, [puz.GridMarkup.Circled])
    assert not m.is_markup_square(1, [puz.GridMarkup.Circled])
    assert m.is_markup_square(2, [puz.GridMarkup.Circled])
    # verify writing produces lowercase in grid and MARK; in REBUS section
    text = puz.to_text_format(p)
    assert '<ACROSS PUZZLE v2>' in text
    assert '\tMARK;' in text
    grid_line = [line for line in text.splitlines() if line.strip().startswith('a')][0]
    assert grid_line == '\taBc'  # circled cells written as lowercase


def test_convert_text_to_puz() -> None:
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


def test_convert_puz_to_text() -> None:
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


def test_invalid_text_format() -> None:
    with pytest.raises(puz.PuzzleFormatError):
        puz.from_text_format('not a valid puzzle')


def test_to_text_format_custom_version() -> None:
    p = puz.read('testfiles/washpost.puz')
    text = puz.to_text_format(p, text_version='v2')
    assert text.startswith('<ACROSS PUZZLE v2>')


def test_to_text_format_invalid_version() -> None:
    p = puz.read('testfiles/washpost.puz')
    with pytest.raises(ValueError):
        puz.to_text_format(p, text_version=None)  # type: ignore


def _make_puzzle() -> puz.Puzzle:
    p = puz.Puzzle()
    p.width = 3
    p.height = 3
    p.solution = 'ABCDEFGHI'
    p.fill = '---------'
    p.clues = ['clue'] * 6
    return p


def test_rebus_add_squares() -> None:
    p = _make_puzzle()
    r = p.rebus()

    # add a single square using int form
    r.add_rebus_squares(4, 'STAR')
    assert r.is_rebus_square(4)
    assert r.get_rebus_solution(4) == 'STAR'
    assert not r.is_rebus_square(0)

    # add multiple squares using list form
    r.add_rebus_squares([0, 8], 'MOON')
    assert r.is_rebus_square(0)
    assert r.get_rebus_solution(0) == 'MOON'
    assert r.is_rebus_square(8)

    # adding the same solution again reuses the existing key (solutions dict doesn't grow)
    n = len(r.solutions)
    r.add_rebus_squares(2, 'STAR')
    assert len(r.solutions) == n
    assert r.get_rebus_solution(2) == 'STAR'


def test_rebus_set_solution() -> None:
    p = _make_puzzle()
    r = p.rebus()
    r.add_rebus_squares(4, 'STAR')

    r.set_rebus_solution(4, 'MOON')
    assert r.get_rebus_solution(4) == 'MOON'

    # set_rebus_solution on a non-rebus square is a no-op
    r.set_rebus_solution(0, 'MOON')
    assert not r.is_rebus_square(0)


def test_check_rebus_fill_non_rebus_square() -> None:
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    r = p.rebus()
    # index 0 is not a rebus square
    assert not r.is_rebus_square(0)
    with pytest.raises(ValueError):
        r.check_rebus_fill(0)


def test_rebus_remove() -> None:
    p = _make_puzzle()
    r = p.rebus()
    r.add_rebus_squares([0, 4, 8], 'STAR')

    # remove a single square using int form
    r.remove_rebus_squares(0)
    assert not r.is_rebus_square(0)
    assert r.is_rebus_square(4)

    # remove multiple squares using list form
    r.remove_rebus_squares([4, 8])
    assert not r.is_rebus_square(4)
    assert not r.is_rebus_square(8)

    # set up for remove_rebus_solution tests
    r.add_rebus_squares([0, 4], 'STAR')
    r.add_rebus_squares([8], 'MOON')

    # remove by string: clears squares that used that solution
    r.remove_rebus_solution('STAR')
    assert not r.is_rebus_square(0)
    assert not r.is_rebus_square(4)
    assert r.is_rebus_square(8)  # MOON square unaffected

    # remove by int key
    moon_key = next(k for k, v in r.solutions.items() if v == 'MOON')
    r.remove_rebus_solution(moon_key)
    assert not r.is_rebus_square(8)

    # remove a non-existent solution string is a no-op (no crash)
    r.remove_rebus_solution('NONEXISTENT')


def test_rebus_add_solution_after_remove() -> None:
    # adding a solution after a removal should not collide with existing keys
    p = _make_puzzle()
    r = p.rebus()
    r.add_rebus_squares(0, 'STAR')   # k=0
    r.add_rebus_squares(4, 'MOON')   # k=1
    r.remove_rebus_solution('STAR')  # solutions={1: 'MOON'}
    r.add_rebus_squares(8, 'HEART')  # must get k=2, not k=1 (which would collide with MOON)
    assert r.get_rebus_solution(4) == 'MOON'
    assert r.get_rebus_solution(8) == 'HEART'
    assert len(r.solutions) == 2


def test_rebus_save_dirty() -> None:
    p = _make_puzzle()
    r = p.rebus()

    # add squares but don't save, then remove them — _dirty=True, no extension ever written
    r.add_rebus_squares([0, 4], 'STAR')
    r.remove_rebus_squares([0, 4])
    assert not r.has_rebus()

    # save should take the _dirty branch and ensure no stale extensions are left
    r.save()
    assert puz.Extensions.Rebus not in p.extensions
    assert puz.Extensions.RebusSolutions not in p.extensions
    assert puz.Extensions.RebusFill not in p.extensions


def test_markup_clear_squares() -> None:
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    m = p.markup()
    squares = m.get_markup_squares()
    assert squares

    # clear a single square using int form
    m.clear_markup_squares(squares[0])
    assert not m.is_markup_square(squares[0])

    # clear multiple squares using list form
    m.clear_markup_squares(squares[1:])
    assert not any(m.is_markup_square(i) for i in squares[1:])
    assert not m.has_markup()


def test_markup_set_single_index() -> None:
    p = _make_puzzle()
    m = p.markup()

    # set_markup_squares with a single int (not a list)
    m.set_markup_squares(4, puz.GridMarkup.Circled)
    assert m.is_markup_square(4)
    assert m.is_markup_square(4, puz.GridMarkup.Circled)


def test_markup_save_dirty() -> None:
    p = _make_puzzle()
    m = p.markup()
    m.set_markup_squares([4], puz.GridMarkup.Circled)
    m.save()
    assert puz.Extensions.Markup in p.extensions

    # clear all markup and save — dirty flag should cause the extension to be removed
    m.clear_markup_squares([4])
    assert not m.has_markup()
    m.save()
    assert puz.Extensions.Markup not in p.extensions


def test_rebus_fill_returns_none_for_non_rebus_square() -> None:
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    assert p.rebus().get_rebus_fill(0) is None


@pytest.mark.parametrize('filename', glob.glob('testfiles/*.txt'))
def test_textfile_roundtrip(filename: str) -> None:
    with open(filename, 'r', encoding='utf-8') as fp:
        orig = fp.read()
        p = puz.read_text(filename)
        new = puz.to_text_format(p)
        assert orig == new, '%s did not round-trip' % filename


def test_helpers_roundtrip() -> None:
    filename = 'testfiles/nyt_rebus_with_notes_and_shape.puz'
    with open(filename, 'rb') as fp:
        orig = fp.read()
    p = puz.read(filename)
    p.rebus()
    p.markup()
    assert orig == p.tobytes()


def test_nonrebus_helpers_roundtrip() -> None:
    filename = 'testfiles/washpost.puz'
    with open(filename, 'rb') as fp:
        orig = fp.read()
    p = puz.read(filename)
    p.rebus()   # side effect: instantiates Rebus helper
    p.markup()  # side effect: instantiates Markup helper
    assert orig == p.tobytes()


def _not_bad(filenames: list[str]) -> list[str]:
    return [f for f in filenames if not f.endswith('_bad.puz')]


@pytest.mark.parametrize('filename', _not_bad(glob.glob('testfiles/*.puz')))
def test_puzfile_roundtrip(filename: str) -> None:
    # test that a .puz file can be read and then written back out without any changes to the bytes
    # purposely doesn't touch markup or rebus to ensure we roundtrip bytes even when the helpers aren't instantiated
    with open(filename, 'rb') as fp:
        orig = fp.read()
        p = puz.read(filename)
        new = p.tobytes()
        assert orig == new, '%s did not round-trip' % filename


@pytest.mark.parametrize('filename', _not_bad(glob.glob('testfiles/*.puz')))
def test_puzfile_roundtrip_with_helpers(filename: str) -> None:
    # variation on the roundtrip test that also instantiates the Rebus, Markup,
    # and Timer helpers to verify that their save methods roundtrip properly
    with open(filename, 'rb') as fp:
        orig = fp.read()
        p = puz.read(filename)
        p.has_rebus()    # side effect: instantiates Rebus helper
        p.has_markup()   # side effect: instantiates Markup helper
        if p.has_timer():
            p.timer()    # side effect: instantiates Timer helper
        new = p.tobytes()
        assert orig == new, '%s did not round-trip' % filename


@pytest.mark.parametrize('filename', glob.glob('testfiles/*_bad.puz'))
def test_bad_puzfile_raises_puzzle_format_error(filename: str) -> None:
    with pytest.raises(puz.PuzzleFormatError):
        puz.read(filename)


def test_timer_running() -> None:
    p = puz.read('testfiles/nyt_partlyfilled.puz')
    assert p.has_timer()
    t = p.timer()
    assert t.elapsed_seconds == 8
    assert t.is_running()


def test_no_timer() -> None:
    p = puz.read('testfiles/washpost.puz')
    assert not p.has_timer()


def test_timer_save_roundtrip() -> None:
    p = _make_puzzle()
    t = p.timer()
    t.elapsed_seconds = 42
    t.status = puz.TimerStatus.Stopped
    p.tobytes()  # triggers save()
    assert p.extensions[puz.Extensions.Timer] == b'42,1'


def test_timer_stopped() -> None:
    p = _make_puzzle()
    p.extensions[puz.Extensions.Timer] = b'120,1'
    t = p.timer()
    assert t.elapsed_seconds == 120
    assert t.is_stopped()


def test_remove_timer() -> None:
    p = puz.read('testfiles/nyt_partlyfilled.puz')
    assert p.has_timer()
    p.timer()  # instantiate helper
    p.remove_timer()
    assert not p.has_timer()
    p.tobytes()  # triggers save() which should remove the extension
    assert puz.Extensions.Timer not in p.extensions


def test_viewer() -> None:
    p = puz.read('testfiles/washpost.puz')
    html = puz_viewer.render_html(p)

    assert '<!DOCTYPE html>' in html
    assert p.title in html
    assert p.author in html

    clues = p.clue_numbering()
    assert clues.across[0].text in html
    assert clues.down[0].text in html

    # one black entry per black square in the puzzle JSON data
    black_count = sum(1 for c in p.solution if puz.is_blacksquare(c))
    assert html.count('"type": "black"') == black_count

    # JS layout engine and structural elements are present
    assert 'const PUZZLE =' in html
    assert 'id="grid"' in html
    assert 'id="content"' in html
    assert '<script>' in html

    # no-title and no-author: original text absent from output
    p2 = puz.read('testfiles/washpost.puz')
    p2.title = ''
    p2.author = ''
    html2 = puz_viewer.render_html(p2)
    assert p.title not in html2
    assert p.author not in html2


def test_viewer_cli(capsys: pytest.CaptureFixture[str]) -> None:
    outfile = temp_filename('html')
    try:
        sys.argv = ['puz_viewer.py', 'testfiles/washpost.puz']
        puz_viewer.main()
        captured = capsys.readouterr()
        assert '<!DOCTYPE html>' in captured.out

        sys.argv = ['puz_viewer.py', 'testfiles/washpost.puz', '-o', outfile]
        puz_viewer.main()
        with open(outfile, encoding='utf-8') as f:
            assert '<!DOCTYPE html>' in f.read()
    finally:
        if os.path.exists(outfile):
            os.unlink(outfile)


def test_viewer_detect_format() -> None:
    with open('testfiles/washpost.puz', 'rb') as f:
        assert puz_viewer._detect_format(f.read()) == 'puz'
    with open('testfiles/text_format_v1.txt', 'rb') as f:
        assert puz_viewer._detect_format(f.read()) == 'txt'


def test_viewer_format_flag(capsys: pytest.CaptureFixture[str]) -> None:
    sys.argv = ['puz_viewer.py', '-f', 'puz', 'testfiles/washpost.puz']
    puz_viewer.main()
    assert '<!DOCTYPE html>' in capsys.readouterr().out

    sys.argv = ['puz_viewer.py', '-f', 'txt', 'testfiles/text_format_v1.txt']
    puz_viewer.main()
    assert '<!DOCTYPE html>' in capsys.readouterr().out


def test_viewer_stdin(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import io
    with open('testfiles/washpost.puz', 'rb') as f:
        data = f.read()

    class FakeStdin:
        def __init__(self) -> None:
            self.buffer = io.BytesIO(data)

    monkeypatch.setattr(sys, 'stdin', FakeStdin())
    sys.argv = ['puz_viewer.py', '-']
    puz_viewer.main()
    assert '<!DOCTYPE html>' in capsys.readouterr().out

    monkeypatch.setattr(sys, 'stdin', FakeStdin())
    sys.argv = ['puz_viewer.py']
    puz_viewer.main()
    assert '<!DOCTYPE html>' in capsys.readouterr().out
