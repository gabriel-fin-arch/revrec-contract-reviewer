"""Writing generated files.

One function, and it exists because of one bug. Python's `write_text` translates
`\\n` to the platform line ending, so every generated file this project writes --
the corpus index, the gold records, the saved eval reports -- came out with CRLF
on Windows and LF everywhere else. All three are committed, so a contributor on
the wrong operating system regenerated them and got a diff touching every line
of every file, with no actual change in any of them.

Passing `newline=""` turns the translation off and writes exactly the string it
was given. Nothing here should ever use `Path.write_text` directly.
"""

from __future__ import annotations

from pathlib import Path


def write_lf(path: Path, content: str) -> Path:
    """Write `content` to `path` with LF line endings on every platform."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    return path
