"""
tests/test_parser.py

Regression tests for gpss/parser.py and gpss/grammar.lark.

Test matrix:
    GI_001  JOEBARB.GPS  — baseline, no labels, tabs, simple operands
    GI_002  barber.gps   — QUEUE/DEPART, TERMINATE with no operands,
                           two-segment model
    GI_003  widgets.gps  — labels, empty operand slots (,,,4), TRANSFER,
                           CLEAR, multi-run control
    GI_004  inspect.gps  — STORAGE, ENTER/LEAVE, fractional probability
                           (.15), START with empty middle operand (5,,1)
"""

from pathlib import Path

import pytest

from gpss.parser import parse_file, RESERVED

# ---------------------------------------------------------------------------
# Model paths
# ---------------------------------------------------------------------------

CLASSIC = Path.home() / "gpss_dev/models/classic"
JOEBARB  = CLASSIC / "JOEBARB.GPS"
BARBER   = CLASSIC / "barber.gps"
WIDGETS  = CLASSIC / "widgets.gps"
INSPECT  = CLASSIC / "inspect.gps"

# ---------------------------------------------------------------------------
# GI_001 — JOEBARB (baseline)
# ---------------------------------------------------------------------------

def test_joebarb_file_exists():
    """JOEBARB.GPS must be reachable via iCloud symlink."""
    assert JOEBARB.exists(), f"Not found: {JOEBARB}"


def test_joebarb_parses_clean():
    """JOEBARB.GPS must produce zero parse errors."""
    result = parse_file(JOEBARB)
    assert result.ok, "Parse errors:\n" + "\n".join(result.errors)


def test_joebarb_produces_tree():
    """A successful parse must return a Lark tree."""
    result = parse_file(JOEBARB)
    assert result.tree is not None


def test_joebarb_statement_count():
    """JOEBARB.GPS has exactly 9 statement lines."""
    result = parse_file(JOEBARB)
    stmts = [l for l in result.lines if l.kind == "statement"]
    assert len(stmts) == 9, f"Expected 9 statements, got {len(stmts)}"


# ---------------------------------------------------------------------------
# Reserved word / label tests (model-independent)
# ---------------------------------------------------------------------------

def test_reserved_includes_key():
    """KEY must be in the RESERVED set (it is an SNA, not a label)."""
    assert "KEY" in RESERVED


def test_label_collision_rejected():
    """A file using a reserved word as a label must produce an error."""
    # widgets.gps originally used KEY as a label — ERROR 94
    # We test this with a synthetic one-liner written to a temp file
    import tempfile, os
    src = "KEY      GENERATE   10\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".GPS", delete=False, encoding="utf-8"
    ) as f:
        f.write(src)
        tmp = f.name
    try:
        result = parse_file(tmp)
        assert not result.ok, "Expected an ERROR 94 but got ok=True"
        assert any("ERROR 94" in e for e in result.errors)
    finally:
        os.unlink(tmp)


# ---------------------------------------------------------------------------
# GI_002 — barber.gps
# ---------------------------------------------------------------------------

def test_barber_file_exists():
    """barber.gps must be reachable via iCloud symlink."""
    assert BARBER.exists(), f"Not found: {BARBER}"


def test_barber_parses_clean():
    """barber.gps must produce zero parse errors."""
    result = parse_file(BARBER)
    assert result.ok, "Parse errors:\n" + "\n".join(result.errors)


def test_barber_statement_count():
    """barber.gps has exactly 12 statement lines."""
    result = parse_file(BARBER)
    stmts = [l for l in result.lines if l.kind == "statement"]
    assert len(stmts) == 12, f"Expected 12 statements, got {len(stmts)}"


# ---------------------------------------------------------------------------
# GI_003 — widgets.gps
# ---------------------------------------------------------------------------

def test_widgets_file_exists():
    """widgets.gps must be reachable via iCloud symlink."""
    assert WIDGETS.exists(), f"Not found: {WIDGETS}"


def test_widgets_parses_clean():
    """widgets.gps must produce zero parse errors."""
    result = parse_file(WIDGETS)
    assert result.ok, "Parse errors:\n" + "\n".join(result.errors)


def test_widgets_statement_count():
    """widgets.gps has exactly 15 statement lines."""
    result = parse_file(WIDGETS)
    stmts = [l for l in result.lines if l.kind == "statement"]
    assert len(stmts) == 15, f"Expected 15 statements, got {len(stmts)}"


# ---------------------------------------------------------------------------
# GI_004 — inspect.gps
# ---------------------------------------------------------------------------

def test_inspect_file_exists():
    """inspect.gps must be reachable via iCloud symlink."""
    assert INSPECT.exists(), f"Not found: {INSPECT}"


def test_inspect_parses_clean():
    """inspect.gps must produce zero parse errors."""
    result = parse_file(INSPECT)
    assert result.ok, "Parse errors:\n" + "\n".join(result.errors)


def test_inspect_statement_count():
    """inspect.gps has exactly 17 statement lines."""
    result = parse_file(INSPECT)
    stmts = [l for l in result.lines if l.kind == "statement"]
    assert len(stmts) == 17, f"Expected 17 statements, got {len(stmts)}"
