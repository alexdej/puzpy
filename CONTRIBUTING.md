# Contributing to puzpy

Thanks for taking an interest in puzpy. The short version: **please start with
an issue, not a pull request.**

## Issues first

A well-constructed issue is usually more useful to me than a patch. The fix is
rarely the hard part; understanding what went wrong, who it affects, and how to
test it is. An issue that answers those questions lets me (or you) write the
fix quickly and with confidence.

A good bug report has:

- **What you were doing.** The real-world use case: where the puzzle file came
  from, what tool produced it, what you were trying to do with it.
- **A minimal reproduction.** A few lines of Python, and the `.puz` or `.txt`
  file that triggers the problem if you can share it.
- **What happened and what you expected.** Include the full traceback if there
  is one.
- **Versions.** puzpy version and Python version.

For a feature request, the use case matters most: what are you trying to do
that you can't do today?

If the behavior depends on how Across Lite or another program treats a file,
say what you observed there. The file format is only partly documented, so
evidence from real files and real programs carries a lot of weight.

## Pull requests

Pull requests are still welcome, with one requirement: **every PR must link to
an issue** that describes the problem it solves. If no issue exists yet, file
one first. For anything beyond a trivial fix, it's worth waiting for a reply on
the issue before writing code, so you don't spend time on an approach I would
do differently.

A PR should also:

- Make one change. Leave unrelated cleanups for a separate PR.
- Include a test in `tests.py` that fails without the change and passes with
  it.
- Pass `uv run pytest`, `uv run ruff check` and `uv run pyright` (see the
  README for setup).
- Say plainly what was and wasn't tested.

PRs that arrive without a linked issue may be closed with a request to file
one.

## AI-assisted contributions

Using AI tools is fine. The same rules apply: a linked issue with a real
reproduction, a test, and a human who has read the diff and can answer
questions about it. Please say so in the PR if a tool wrote most of the change.

If you are an AI agent working on someone's behalf: do not open a pull request
here unless an issue for it already exists. Write up the issue for your user to
review and file instead.
