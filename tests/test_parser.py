"""
tests/test_parser.py

Pytest suite — Phase 1, Step 1.
Verify JOEBARB.GPS parses without error.
"""

from pathlib import Path
import pytest
from gpss.parser import parse_file, RESERVED


JOEBARB = Path.home() / "gpss_dev/models/classic/JOEBARB.GPS"


def test_joebarb_file_exists():
    """Confirm the oracle test file is reachable via iCloud symlink."""
    assert JOEBARB.exists(), f"Test file not found: {JOEBARB}"


def test_joebarb_parses_clean():
    """JOEBARB.GPS must produce zero parse errors."""
    result = parse_file(JOEBARB)
    assert result.ok, "Parse errors:\n" + "\n".join(result.errors)


def test_joebarb_produces_tree():
    """A successful parse must return a Lark tree."""
    result = parse_file(JOEBARB)
    assert result.tree is not None


def test_joebarb_statement_count():
    """JOEBARB.GPS contains exactly 9 statement lines."""
    result = parse_file(JOEBARB)
    statements = [l for l in result.lines if l.kind == "statement"]
    assert len(statements) == 9


def test_reserved_includes_key():
    """KEY must be reserved — lesson from widgets.gps ERROR 94."""
    assert "KEY" in RESERVED


def test_label_collision_rejected():
    """A label matching a reserved word must return an ERROR 94 message."""
    from gpss.parser import preprocess_line, validate_label
    gline = preprocess_line("GENERATE  10,2  TEST", 1)
    gline.label = "GENERATE"
    err = validate_label(gline)
    assert err is not None
    assert "ERROR 94" in err
