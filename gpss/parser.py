"""
gpss/parser.py

GPSS/H source file preprocessor and Lark parser.

Responsibilities:
    1. Read raw GPSS/H source lines
    2. Classify each line: comment, blank, or statement
    3. Extract label, keyword, operands, comment fields
    4. Validate labels against reserved word and SNA tables
    5. Feed normalized text to Lark for grammar validation

Column conventions (GPSS/H Release 2.01):
    Cols 1-8:   Label field — optional, must start in col 1
    Col  9:     Mandatory blank separator
    Cols 10-18: Keyword field
    Col  19+:   Operands then inline comment
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from lark import Lark, Tree


# ---------------------------------------------------------------------------
# Reserved word tables
# ---------------------------------------------------------------------------

GPSS_KEYWORDS: frozenset[str] = frozenset({
    "SIMULATE", "GENERATE", "ADVANCE", "SEIZE", "RELEASE",
    "TERMINATE", "START", "END", "QUEUE", "DEPART",
    "ENTER", "LEAVE", "TRANSFER", "TEST", "SAVEVALUE",
    "LOGIC", "GATE", "PREEMPT", "RETURN", "SPLIT",
    "ASSEMBLE", "MATCH", "LINK", "UNLINK", "PRIORITY",
    "MARK", "TABULATE", "GATHER", "COUNT", "SELECT",
    "WRITE", "PRINT", "BPUTPIC", "PUTPIC", "GETLIST",
    "BLET", "LET", "CLEAR", "RESET", "RMULT",
    "STORAGE", "FUNCTION", "TABLE", "QTABLE", "MATRIX",
    "INITIAL", "FILEDEF", "EQU", "UNLIST", "LIST",
    "DO", "ENDDO", "IF", "ENDIF", "ELSE",
    "INTEGER", "REAL", "BVARIABLE", "VARIABLE",
})

GPSS_SNAS: frozenset[str] = frozenset({
    "AC1", "C1", "CH", "CL", "CM", "CR", "CT",
    "FC", "FR", "FT", "FI", "FNI",
    "K", "KEY", "M1", "MB", "MH", "ML", "MS", "MX",
    "N", "P", "PB", "PF", "PH", "PL", "PW",
    "Q", "QA", "QB", "QC", "QD", "QM", "QT", "QX", "QZ",
    "R", "RN", "S", "SA", "SC", "SE", "SF", "SM", "SR", "ST", "SV",
    "T", "TB", "TC", "TD", "TG", "TH", "TM", "TR",
    "W", "WM", "X", "XB", "XF", "XH", "XL",
})

RESERVED: frozenset[str] = GPSS_KEYWORDS | GPSS_SNAS


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class GpssLine:
    """One preprocessed line from a GPSS/H source file."""

    line_number: int
    raw: str
    kind: str                    # 'comment' | 'blank' | 'statement'
    label: Optional[str] = None
    keyword: Optional[str] = None
    operands: Optional[str] = None
    comment: Optional[str] = None


@dataclass
class ParseResult:
    """Result returned by parse_file()."""

    lines: list[GpssLine] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tree: Optional[Tree] = None

    @property
    def ok(self) -> bool:
        """True when no errors were found."""
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Line preprocessor
# ---------------------------------------------------------------------------

def preprocess_line(raw: str, line_number: int) -> GpssLine:
    """
    Classify and decompose one raw GPSS/H source line.

    Args:
        raw:         Raw text of the line, newline already stripped.
        line_number: 1-based line number for error reporting.

    Returns:
        GpssLine with kind and fields populated.
    """
    # Blank line
    if raw.strip() == "":
        return GpssLine(line_number=line_number, raw=raw, kind="blank")

    # Comment line — asterisk in column 1
    if raw[0] == "*":
        return GpssLine(line_number=line_number, raw=raw, kind="comment")

    # Statement line
    # Col 1 non-blank and non-tab means a label is present
    if raw[0] not in (" ", "\t"):
        m = re.match(r'^([A-Z$#@][A-Z0-9$#@]{0,7})\s+(.*)', raw)
        if not m:
            return GpssLine(
                line_number=line_number,
                raw=raw,
                kind="statement",
                comment=f"WARNING: unrecognized label format at line {line_number}",
            )
        label: Optional[str] = m.group(1)
        rest = m.group(2)
    else:
        label = None
        rest = raw.lstrip(" \t")

    # Split rest into keyword / operands / comment
    # Fields are separated by whitespace (spaces or tabs)
    parts = re.split(r'[ \t]+', rest, maxsplit=2)
    keyword = parts[0].upper() if parts else None
    operands = parts[1] if len(parts) > 1 else None
    comment = parts[2] if len(parts) > 2 else None

    return GpssLine(
        line_number=line_number,
        raw=raw,
        kind="statement",
        label=label,
        keyword=keyword,
        operands=operands,
        comment=comment,
    )


def validate_label(gline: GpssLine) -> Optional[str]:
    """
    Verify a label is not a reserved word or SNA name.

    Args:
        gline: A preprocessed statement line.

    Returns:
        Error string if invalid, None if OK.
    """
    if gline.label and gline.label.upper() in RESERVED:
        return (
            f"Line {gline.line_number}: label '{gline.label}' "
            f"is a reserved word or SNA (GPSS/H ERROR 94)"
        )
    return None


# ---------------------------------------------------------------------------
# Lark grammar loader
# ---------------------------------------------------------------------------

def _load_grammar() -> Lark:
    """
    Load the Lark grammar from grammar.lark in the same directory.

    Returns:
        Configured Lark parser instance.
    """
    grammar_path = Path(__file__).parent / "grammar.lark"
    grammar_text = grammar_path.read_text(encoding="utf-8")
    return Lark(grammar_text, parser="earley", ambiguity="resolve")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_file(path: str | Path) -> ParseResult:
    """
    Parse a GPSS/H source file.

    Args:
        path: Path to the .GPS source file.

    Returns:
        ParseResult containing preprocessed lines, errors, and Lark tree.
    """
    result = ParseResult()
    source_path = Path(path)

    if not source_path.exists():
        result.errors.append(f"File not found: {source_path}")
        return result

    raw_lines = source_path.read_text(encoding="utf-8").splitlines()

    # Preprocess every line
    for i, raw in enumerate(raw_lines, start=1):
        gline = preprocess_line(raw, i)
        result.lines.append(gline)

        if gline.kind == "statement":
            err = validate_label(gline)
            if err:
                result.errors.append(err)

    if result.errors:
        return result

    # Build normalized source for Lark — one line per statement
    normalized_lines: list[str] = []
    for gline in result.lines:
        if gline.kind == "blank":
            normalized_lines.append("")
        elif gline.kind == "comment":
            normalized_lines.append(gline.raw)
        else:
            parts: list[str] = []
            if gline.label:
                parts.append(f"{gline.label} ")
            parts.append(gline.keyword or "")
            if gline.operands:
                parts.append(f" {gline.operands}")
            normalized_lines.append("".join(parts))

    normalized = "\n".join(normalized_lines) + "\n"

    # Parse with Lark
    try:
        parser = _load_grammar()
        result.tree = parser.parse(normalized)
    except Exception as exc:
        result.errors.append(f"Parse error: {exc}")

    return result
