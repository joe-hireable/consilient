"""The string grammar behind C3: is this text really DDL, and does sqlite accept it?

Nothing here parses Python or touches the filesystem. It reads a string and decides —
which is a different subject from walking a syntax tree and a different subject again
from driving a command line, and it is the part of the check that carries the precision.

`_create_table_shaped`, with `_after_table_name` under it, is what stops the naive walk
from firing on the regex in `scripts/build_diagrams.py` and on the Python-source fixture
in `tests/test_build_diagrams.py` [measured]. Neither is DDL, and both contain the
words. `_without_leading_sql_comments` lets a script that opens with `--` or `/* */`
still be recognised.

`_ddl_slice` carries its own measurement: a CREATE TABLE match can sit embedded inside a
larger non-SQL string, and running the whole original string through sqlite would drag
in whatever follows the real DDL and raise a syntax error that says nothing about
whether the DDL is sound. It trims to the last statement boundary; a script with no
closing semicolon — the truncated-mid-statement case the check exists to catch — is used
unchanged.

`_ddl_start`, which scans statement boundaries using all of this, stays in the gate
rather than joining it here. It holds the literal `create table`, and that literal is
itself DDL-shaped by its own rule, so it can only live in the one file the C3 sweep
exempts [measured 28 August 2026]."""

import sqlite3
import sys
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _without_leading_sql_comments(value: str) -> str:
    text = value.lstrip()
    while text:
        if text.startswith("--"):
            _, separator, text = text.partition("\n")
            if not separator:
                return ""
            text = text.lstrip()
            continue
        if text.startswith("/*"):
            end = text.find("*/", 2)
            if end < 0:
                return ""
            text = text[end + 2 :].lstrip()
            continue
        break
    return text


def _after_table_name(value: str) -> str | None:
    if not value:
        return ""
    if value[0] in {'"', "`", "["}:
        closing = "]" if value[0] == "[" else value[0]
        end = value.find(closing, 1)
        return "" if end < 0 else value[end + 1 :].lstrip()
    end = 0
    while end < len(value) and (value[end].isalnum() or value[end] in "_.$"):
        end += 1
    if end == 0:
        return None
    return value[end:].lstrip()


def _create_table_shaped(tail: str) -> bool:
    """Does `tail` (already past a "create table" match) look like real DDL?"""
    if tail and not tail[0].isspace():
        return False
    tail = tail.lstrip()
    conditional = "if not exists"
    if tail.casefold().startswith(conditional):
        remainder = tail[len(conditional) :]
        if not remainder or remainder[0].isspace():
            tail = remainder.lstrip()
    after_name = _after_table_name(tail)
    if after_name is None:
        return False
    if not after_name:
        return True
    folded = after_name.casefold()
    return (
        after_name.startswith(("(", ";")) or folded == "as" or folded.startswith("as ")
    )


def _ddl_slice(value: str, start: int) -> str:
    """The DDL statement(s) at `start`, trimmed of anything trailing the last ';'.

    A CREATE TABLE match can sit embedded inside a larger non-SQL string (Python
    source text being written out as a file, in `test_build_diagrams.py`'s own
    fixtures) -- running the WHOLE original string through sqlite from `start`
    onward would drag in whatever non-SQL text follows the real DDL (a closing
    docstring quote, more Python) and raise a syntax error that has nothing to do
    with whether the DDL itself is sound. Trim to the last statement boundary at
    or after `start`; a script with no closing ';' (the truncated-mid-statement
    case this check exists to catch) is used unchanged.
    """
    last_semicolon = value.rfind(";", start)
    if last_semicolon < 0:
        return value[start:]
    return value[start : last_semicolon + 1]


def _ddl_error(script: str) -> sqlite3.Error | None:
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(script)
    except sqlite3.Error as error:
        return error
    finally:
        connection.close()
    return None
