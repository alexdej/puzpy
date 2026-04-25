#!/usr/bin/env python3
"""Sync viewer_template.html into puz_viewer.py's _TEMPLATE string literal.

The template is a standalone HTML file with real puzzle data for browser testing.
This script replaces the puzzle data and title with placeholders (__PUZZLE_DATA__,
__TITLE__) and embeds the result as _TEMPLATE in puz_viewer.py.

Usage:
    python sync_template.py              # dry-run (shows diff)
    python sync_template.py --write      # overwrite puz_viewer.py
"""
import re
import sys

TEMPLATE = 'viewer_template.html'
TARGET = 'puz_viewer.py'


def templatize(html: str) -> str:
    """Replace puzzle-specific data with placeholders."""
    # Replace <title>...</title> with placeholder
    result = re.sub(
        r'<title>.*?</title>',
        '<title>__TITLE__</title>',
        html,
    )
    # Replace const PUZZLE = {...}; with placeholder
    return re.sub(
        r'const PUZZLE = \{.*?\};',
        'const PUZZLE = __PUZZLE_DATA__;',
        result,
    )


def main() -> None:
    write = '--write' in sys.argv

    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()

    template_str = templatize(html)

    with open(TARGET, encoding='utf-8') as f:
        original = f.read()

    # Replace the _TEMPLATE string literal content
    m = re.search(
        r'(_TEMPLATE = """\\\n)(.*?)(""")',
        original,
        re.DOTALL,
    )
    if not m:
        print(f'ERROR: Could not find _TEMPLATE = """\\....""" in {TARGET}',
              file=sys.stderr)
        sys.exit(1)

    result = (
        original[:m.start()]
        + '_TEMPLATE = """\\\n'
        + template_str
        + '"""'
        + original[m.end():]
    )

    if result == original:
        print('No changes needed.')
        return

    if write:
        with open(TARGET, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f'Updated {TARGET} from {TEMPLATE}.')
    else:
        old_lines = original.count('\n')
        new_lines = result.count('\n')
        print(f'Dry run: {TARGET} would change ({old_lines} -> {new_lines} lines).')
        print(f'  template: {len(template_str)} chars')
        print('Run with --write to apply.')


if __name__ == '__main__':
    main()
