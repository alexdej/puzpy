import argparse
import html as html_lib
import json
import os
import sys
from typing import Any

import puz

# Generated from viewer_template.html — do not edit directly.
# Run `make template` (or `python sync_template.py --write`) to update.
_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>__TITLE__</title>
<style>
@page { size: letter; margin: 0.5in; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Times New Roman', Georgia, serif;
  background: white;
  display: flex; justify-content: center; align-items: flex-start;
  padding: 0.25in;
  min-width: 7.5in;
  overflow: auto;
}
@media print {
  body { padding: 0; display: block; min-width: 0; overflow: visible; }
}
.page {
  width: 7.5in; height: 10in; background: white;
  min-width: 7.5in; min-height: 10in;
  max-width: 7.5in; max-height: 10in;
  padding: 0;
  display: flex; flex-direction: column; overflow: hidden;
  flex-shrink: 0;
}
.puzzle-title {
  font-size: 14pt; font-weight: bold; margin-bottom: 4px; line-height: 1.2;
}
.title-rule { border: none; border-top: 1.5px solid #000; margin-bottom: 6px; }
.content-area { flex: 1; position: relative; overflow: hidden; }
.grid-wrap { position: absolute; top: 0; }
.grid-table {
  border-collapse: separate;
  border-spacing: 0;
  border-right: 2px solid #000;
  border-bottom: 2px solid #000;
  border-top: none;
  border-left: none;
}
.grid-table td {
  border-top: 2px solid #000;
  border-left: 2px solid #000;
  border-right: none;
  border-bottom: none;
  position: relative; vertical-align: top; padding: 0;
}
.grid-table td.black {
  background: #000;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.clue-col { position: absolute; overflow: hidden; }
.clue-section-header {
  font-weight: bold; margin-bottom: 0; break-after: avoid;
}
.clue-section-header.down-header { margin-top: 12px; }
.clue-item { margin-bottom: 0; }
.clue-number { font-weight: bold; display: inline-block; text-align: right; }
.footer-rule { border: none; border-top: 1px solid #000; margin-bottom: 4px; }
.footer {
  display: flex; justify-content: space-between;
  align-items: baseline; font-size: 8pt;
}
.footer-copyright { font-size: 7.5pt; }
</style>
</head>
<body>
<div class="page">
  <div class="puzzle-title" id="title"></div>
  <hr class="title-rule">
  <div class="content-area" id="content">
    <div class="grid-wrap" id="gridWrap">
      <table class="grid-table" id="grid"></table>
    </div>
  </div>
  <hr class="footer-rule">
  <div class="footer">
    <span id="author"></span>
    <span class="footer-copyright" id="copyright"></span>
  </div>
</div>
<script>
const PUZZLE = __PUZZLE_DATA__;
const S = (() => {
  const n = Math.max(PUZZLE.width, PUZZLE.height);
  const pageW = 720;
  const isSmall = n <= 10;
  const isLarge = n > 15;
  const cellSize = isSmall ? Math.min(32, Math.floor(pageW * 0.35 / n))
    : Math.min(26, Math.floor(pageW * 0.58 / n));
  return {
    cellSize,
    isSmall,
    isLarge,
    cellNumFont: cellSize >= 30 ? '8pt' : cellSize >= 24 ? '6.3pt' : '5.5pt',
    cellNumLeft: cellSize >= 30 ? '2px' : cellSize >= 24 ? '2px' : '1px',
    cellNumTop: cellSize >= 30 ? '1.5px' : cellSize >= 24 ? '1px' : '0.5px',
    numLeftCols: isSmall ? 1 : isLarge ? 3 : 2,
    numRightCols: isSmall ? 2 : isLarge ? 4 : 2,
    colGap: isLarge ? 10 : 14,
    gridGapX: isLarge ? 12 : 16,
    gridGapY: isSmall ? 16 : isLarge ? 8 : 10,
    clueFontSize: isSmall ? '11pt' : isLarge ? '9pt' : '10.5pt',
    clueLineHeight: isSmall ? '1.35' : isLarge ? '1.25' : '1.3',
    headerFontSize: isSmall ? '12pt' : isLarge ? '9.5pt' : '11pt',
    numWidth: '17px',
    numMargin: '3px',
    clueIndent: '20px'
  };
})();

document.head.insertAdjacentHTML('beforeend', `<style>
  .grid-table td { width: ${S.cellSize}px; height: ${S.cellSize}px; }
  .cell-number {
    position: absolute; top: ${S.cellNumTop}; left: ${S.cellNumLeft};
    font-size: ${S.cellNumFont}; line-height: 1;
  }
  .clue-col { font-size: ${S.clueFontSize}; line-height: ${S.clueLineHeight}; }
  .clue-section-header {
    font-size: ${S.headerFontSize}; padding-left: ${S.clueIndent};
  }
  .clue-item { padding-left: ${S.clueIndent}; text-indent: -${S.clueIndent}; }
  .clue-number { width: ${S.numWidth}; margin-right: ${S.numMargin}; }
</style>`);

function buildGrid() {
  const table = document.getElementById('grid');
  const { width, height, grid } = PUZZLE;
  const lookup = {};
  grid.forEach(c => { lookup[c.row + ',' + c.col] = c; });
  for (let r = 0; r < height; r++) {
    const tr = document.createElement('tr');
    for (let c = 0; c < width; c++) {
      const cell = lookup[r + ',' + c];
      const td = document.createElement('td');
      if (!cell || cell.type === 'black') {
        td.className = 'black';
      } else if (cell.number) {
        const span = document.createElement('span');
        span.className = 'cell-number';
        span.textContent = cell.number;
        td.appendChild(span);
      }
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
}

function buildClueElements() {
  const items = [];
  const acrossH = document.createElement('div');
  acrossH.className = 'clue-section-header';
  acrossH.textContent = 'ACROSS';
  items.push(acrossH);
  PUZZLE.clues.across.forEach(c => {
    const div = document.createElement('div');
    div.className = 'clue-item';
    div.innerHTML =
      '<span class="clue-number">' + c.number + '</span> ' + c.text;
    items.push(div);
  });
  const downH = document.createElement('div');
  downH.className = 'clue-section-header down-header';
  downH.textContent = 'DOWN';
  items.push(downH);
  PUZZLE.clues.down.forEach(c => {
    const div = document.createElement('div');
    div.className = 'clue-item';
    div.innerHTML =
      '<span class="clue-number">' + c.number + '</span> ' + c.text;
    items.push(div);
  });
  return items;
}

function tryLayout(bottomY, H, colGeom, items, content) {
  content.querySelectorAll('.clue-col').forEach(el => el.remove());

  // Reset margins from any previous justification pass
  items.forEach(item => { item.style.marginBottom = ''; });

  const colDivs = colGeom.map(c => {
    const top = c.isLeft ? 0 : c.y;
    const h = c.isLeft ? bottomY : (bottomY - c.y);
    const div = document.createElement('div');
    div.className = 'clue-col';
    div.style.left = c.x + 'px';
    div.style.top = top + 'px';
    div.style.width = c.w + 'px';
    div.style.height = h + 'px';
    content.appendChild(div);
    return { div, maxH: h };
  });

  let colIdx = 0;
  for (let idx = 0; idx < items.length; idx++) {
    const item = items[idx];
    if (colIdx >= colDivs.length) {
      colDivs[colDivs.length - 1].div.appendChild(item);
      continue;
    }
    const col = colDivs[colIdx];
    col.div.appendChild(item);
    if (col.div.scrollHeight > col.maxH) {
      col.div.removeChild(item);
      colIdx++;
      if (colIdx >= colDivs.length) {
        colDivs[colDivs.length - 1].div.appendChild(item);
      } else {
        colDivs[colIdx].div.appendChild(item);
      }
    } else if (item.classList.contains('clue-section-header') && idx + 1 < items.length) {
      // Header fits, but check if at least one clue fits after it
      const nextItem = items[idx + 1];
      col.div.appendChild(nextItem);
      if (col.div.scrollHeight > col.maxH) {
        // Won't fit — move header to next column
        col.div.removeChild(nextItem);
        col.div.removeChild(item);
        colIdx++;
        if (colIdx >= colDivs.length) {
          colDivs[colDivs.length - 1].div.appendChild(item);
          colDivs[colDivs.length - 1].div.appendChild(nextItem);
        } else {
          colDivs[colIdx].div.appendChild(item);
          colDivs[colIdx].div.appendChild(nextItem);
        }
        idx++;  // skip next item, already placed
      } else {
        // Both fit — remove nextItem, let the loop place it normally
        col.div.removeChild(nextItem);
      }
    }
  }

  const lastCol = colDivs[colDivs.length - 1];
  return colDivs.every(c => c.div.scrollHeight <= c.maxH);
}

function layoutClues() {
  const content = document.getElementById('content');
  const gridWrap = document.getElementById('gridWrap');

  const W = content.offsetWidth;
  const H = content.offsetHeight;
  const gW = gridWrap.offsetWidth;
  const gH = gridWrap.offsetHeight;

  // Cap: never wider than what a 15x15 two-column layout produces (~160px)
  const maxColW = 160;
  const naturalLeftColW = (W - gW - S.gridGapX - (S.numLeftCols - 1) * S.colGap) / S.numLeftCols;
  const leftColW = Math.min(maxColW, naturalLeftColW);
  const rightColTop = gH + S.gridGapY;
  const rightColW = (gW - (S.numRightCols - 1) * S.colGap) / S.numRightCols;

  // Build geometry relative to x=0: left cols, then grid, then right cols under grid
  const leftColsTotalW = S.numLeftCols * leftColW + (S.numLeftCols - 1) * S.colGap;
  const gridLeft = leftColsTotalW + S.gridGapX;
  const blockW = gridLeft + gW;

  const colGeom = [];
  for (let i = 0; i < S.numLeftCols; i++) {
    colGeom.push({
      x: i * (leftColW + S.colGap),
      y: 0,
      w: leftColW,
      isLeft: true
    });
  }
  for (let i = 0; i < S.numRightCols; i++) {
    colGeom.push({
      x: gridLeft + i * (rightColW + S.colGap),
      y: rightColTop,
      w: rightColW,
      isLeft: false
    });
  }

  const items = buildClueElements();

  // Try left-only layout: skip the L-shape if clues fit next to the grid
  let usedLeftOnly = false;
  const leftOnlyMaxH = Math.ceil(gH * 1.25);
  if (leftOnlyMaxH < H) {
    const leftOnlyGeom = colGeom.filter(c => c.isLeft);
    if (tryLayout(leftOnlyMaxH, leftOnlyMaxH, leftOnlyGeom, items, content)) {
      usedLeftOnly = true;
    }
  }

  if (!usedLeftOnly) {
    // L-shaped layout — binary search for balanced bottomY
    let lo = Math.ceil(rightColTop + 60);
    let hi = H;
    let bestY = H;

    for (let i = 0; i < 25; i++) {
      const mid = Math.floor((lo + hi) / 2);
      const fits = tryLayout(mid, H, colGeom, items, content);
      if (fits) {
        bestY = mid;
        hi = mid;
      } else {
        lo = mid + 1;
      }
    }

    let finalY = Math.min(bestY + 5, H);
    for (let attempt = 0; attempt < 10; attempt++) {
      tryLayout(finalY, H, colGeom, items, content);
      const cols = content.querySelectorAll('.clue-col');
      let maxOverflow = 0;
      cols.forEach(c => {
        const ov = c.scrollHeight - c.clientHeight;
        if (ov > maxOverflow) maxOverflow = ov;
      });
      if (maxOverflow <= 0) break;
      finalY = Math.min(finalY + maxOverflow + 2, H);
    }
  }

  // Rebalance columns
  const allCols = content.querySelectorAll('.clue-col');
  const colArr = Array.from(allCols);

  function getSlackPerGap(col) {
    const kids = Array.from(col.children);
    if (kids.length < 2) return 9999;
    let contentH = 0;
    kids.forEach(k => { contentH += k.offsetHeight; });
    const slack = col.clientHeight - contentH;
    return slack / (kids.length - 1);
  }

  for (let pass = 0; pass < 20; pass++) {
    let moved = false;
    for (let i = colArr.length - 2; i >= 0; i--) {
      const curr = colArr[i];
      const next = colArr[i + 1];
      if (curr.children.length < 3) continue;
      const currSpg = getSlackPerGap(curr);
      const nextSpg = getSlackPerGap(next);
      if (nextSpg < currSpg * 1.5) continue;
      const item = curr.lastChild;
      curr.removeChild(item);
      next.insertBefore(item, next.firstChild);
      if (next.scrollHeight > next.clientHeight) {
        next.removeChild(item);
        curr.appendChild(item);
      } else {
        moved = true;
      }
    }
    if (!moved) break;
  }

  // Vertically justify using flexbox space-between (skip for left-only layout)
  if (!usedLeftOnly) {
    colArr.forEach(col => {
      col.style.display = 'flex';
      col.style.flexDirection = 'column';
      col.style.justifyContent = 'space-between';
    });
  }

  // Center the entire block on the page
  const offsetX = Math.max(0, (W - blockW) / 2);
  gridWrap.style.left = (gridLeft + offsetX) + 'px';
  colArr.forEach(col => {
    col.style.left = (parseFloat(col.style.left) + offsetX) + 'px';
  });
}

document.getElementById('title').textContent = PUZZLE.title;
document.getElementById('author').textContent = PUZZLE.author;
if (PUZZLE.copyright) {
  document.getElementById('copyright').textContent = PUZZLE.copyright;
}

buildGrid();

function doLayout() {
  requestAnimationFrame(() => { requestAnimationFrame(layoutClues); });
}
doLayout();
window.addEventListener('beforeprint', layoutClues);
window.addEventListener('afterprint', layoutClues);
</script>
</body>
</html>
"""


def _puzzle_data(puzzle: puz.Puzzle) -> dict[str, Any]:
    clues = puzzle.clue_numbering()
    numbered: dict[int, int] = {}
    for clue in clues.across + clues.down:
        if clue.cell not in numbered:
            numbered[clue.cell] = clue.number

    diagramless = puzzle.puzzletype == puz.PuzzleType.Diagramless

    grid_cells = []
    for i, ch in enumerate(puzzle.solution):
        cell: dict[str, Any] = {
            'index': i, 'row': i // puzzle.width, 'col': i % puzzle.width
        }
        if diagramless:
            cell['type'] = 'white'
        elif puz.is_blacksquare(ch):
            cell['type'] = 'black'
        else:
            cell['type'] = 'white'
            if i in numbered:
                cell['number'] = numbered[i]
        grid_cells.append(cell)

    return {
        'title': puzzle.title or '',
        'author': puzzle.author or '',
        'copyright': puzzle.copyright or '',
        'width': puzzle.width,
        'height': puzzle.height,
        'grid': grid_cells,
        'clues': {
            'across': [
                {'number': c.number, 'text': c.text} for c in clues.across
            ],
            'down': [
                {'number': c.number, 'text': c.text} for c in clues.down
            ],
        }
    }


def _detect_format(data: bytes) -> str:
    if b'ACROSS&DOWN' in data:
        return 'puz'
    if b'<ACROSS PUZZLE' in data:
        return 'txt'
    raise ValueError('Cannot detect puzzle format from input data')


def render_html(puzzle: puz.Puzzle) -> str:
    data = _puzzle_data(puzzle)
    puzzle_json = json.dumps(data, ensure_ascii=False)
    page_title = (
        html_lib.escape(puzzle.title, quote=False) if puzzle.title
        else 'Crossword'
    )
    return (
        _TEMPLATE
        .replace('__TITLE__', page_title)
        .replace('__PUZZLE_DATA__', puzzle_json)
    )


_INDEX_CSS = """\
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica,
    Arial, sans-serif;
  color: #1f2328; background: #fff; line-height: 1.5;
  max-width: 640px; margin: 0 auto; padding: 40px 24px;
}
h1 { font-size: 24px; font-weight: 600; margin-bottom: 8px; }
.subtitle { font-size: 14px; color: #656d76; margin-bottom: 24px; }
ul { list-style: none; }
li { border-top: 1px solid #d1d9e0; }
li:last-child { border-bottom: 1px solid #d1d9e0; }
a {
  display: block; padding: 10px 4px; color: #0969da;
  text-decoration: none; font-size: 14px;
}
a:hover { background: #f6f8fa; }
"""


def _generate_index(directory: str, files: list[str]) -> None:
    items = '\n'.join(
        f'<li><a href="{f}">{f}</a></li>' for f in sorted(files)
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>puzpy viewer</title>
<style>
{_INDEX_CSS}
</style>
</head>
<body>
<h1>puzpy viewer</h1>
<p class="subtitle">Sample crossword puzzles rendered by puz_viewer</p>
<ul>
{items}
</ul>
</body>
</html>"""
    with open(os.path.join(directory, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)


def _load_puzzle(raw: bytes, fmt: str) -> puz.Puzzle:
    resolved = fmt if fmt != 'auto' else _detect_format(raw)
    if resolved == 'puz':
        return puz.load(raw)
    return puz.load_text(raw.decode())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an HTML viewer for a crossword puzzle or puzzles"
    )
    parser.add_argument(
        'puzzles', nargs='*', default=['-'],
        help="Paths to .puz or .txt files (default: stdin)"
    )
    parser.add_argument(
        '-o', '--outfile',
        help="Output HTML filename (default: stdout, or auto-generated from input filename in batch mode)"
    )
    parser.add_argument(
        '--outdir', help="Output directory for HTML files (default: .)"
    )
    parser.add_argument(
        '-f', '--format', choices=['auto', 'puz', 'txt'], default='auto',
        help="Input format (default: auto-detect)"
    )
    parser.add_argument(
        '--index', action='store_true',
        help="Generate index.html in output directory (batch mode)"
    )
    args = parser.parse_args()

    outdir = args.outdir or '.'

    def default_outfile(src: str) -> str:
        base = os.path.splitext(os.path.basename(src))[0]
        return base + '.html'

    # Single file mode: one puzzle to stdout or -o file
    if len(args.puzzles) == 1 and not args.index:
        src = args.puzzles[0]
        if src == '-':
            raw = sys.stdin.buffer.read()
        else:
            with open(src, 'rb') as f:
                raw = f.read()
        p = _load_puzzle(raw, args.format)
        out = render_html(p)
        if args.outfile or args.outdir:
            outfile = os.path.join(outdir, args.outfile or default_outfile(src))
            with open(outfile, 'w', encoding='utf-8') as fout:
                fout.write(out)
        else:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            sys.stdout.write(out)
        return

    # Batch mode: multiple puzzles to output directory
    os.makedirs(outdir, exist_ok=True)
    generated: list[str] = []
    for src in args.puzzles:
        name = default_outfile(src)
        try:
            with open(src, 'rb') as f:
                raw = f.read()
            p = _load_puzzle(raw, args.format)
            out = render_html(p)
            with open(os.path.join(outdir, name), 'w', encoding='utf-8') as fout:
                fout.write(out)
            generated.append(name)
            print(f'OK: {src}', file=sys.stderr)
        except Exception as e:
            print(f'SKIP: {src} ({e})', file=sys.stderr)

    if args.index:
        _generate_index(outdir, generated)


if __name__ == '__main__':
    main()
