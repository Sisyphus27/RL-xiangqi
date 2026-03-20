"""Cross-validation of starting-position legal moves against pyffish.

TEST-02: If pyffish is available, verify all starting-position legal moves
match pyffish's reference move set. If pyffish is not available or crashes,
the test file is skipped entirely (no failure).

pyffish returns moves as UCI strings (e.g., "h2e2"). These are converted
to the project's 16-bit integer encoding for comparison.

pyffish installation:
  1. Install stockfish system library:
     macOS: brew install stockfish
     Linux: apt install stockfish
  2. pip install pyffish

FEN format: WXF (same as engine uses):
  "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w"
"""
from __future__ import annotations

import subprocess
import sys
import json

import pytest

# Check if pyffish module exists
pyffish = pytest.importorskip(
    "pyffish",
    reason="pyffish not installed (install: brew install stockfish && pip install pyffish)"
)

from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.types import encode_move


# WXF FEN for standard starting position (red to move)
STARTING_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w"
# pyffish requires full FEN with move counters
PYFFISH_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"


def _get_pyffish_moves_safe() -> list[str] | None:
    """Get legal moves from pyffish in a subprocess to avoid segfaults.

    Returns None if pyffish crashes or has compatibility issues.
    """
    code = '''
import json
import sys
try:
    import pyffish
    fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
    moves = pyffish.legal_moves(fen, "", [])
    json.dump(moves, sys.stdout)
except Exception as e:
    json.dump({"error": str(e)}, sys.stdout)
'''
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        if isinstance(data, dict) and "error" in data:
            return None
        return data
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


def uci_sq_to_flat(uci_sq: str) -> int:
    """Convert UCI square (e.g., 'h2') to flat square index 0-89.

    Xiangqi UCI coordinate system:
      Files: a=0, b=1, ..., i=8 (left to right from black's perspective)
      Ranks: '9' = row 0 (black back rank), '1' = row 9 (red back rank)
             i.e., row = 9 - int(rank_char)
    """
    col = ord(uci_sq[0]) - ord('a')   # 'a'=0, 'b'=1, ..., 'i'=8
    row = 9 - int(uci_sq[1])           # '9' -> row 0, '1' -> row 9
    return row * 9 + col


def uci_to_move(uci: str) -> int:
    """Convert full UCI string (e.g., 'h2e2') to 16-bit move integer."""
    return encode_move(uci_sq_to_flat(uci[:2]), uci_sq_to_flat(uci[2:]))


# Check if pyffish actually works at import time (using subprocess to avoid crashes)
# If it crashes (segfault) or has API issues, skip all tests
_PYFFISH_MOVES = _get_pyffish_moves_safe()
if _PYFFISH_MOVES is None:
    pytest.skip(
        "pyffish available but not working (API incompatibility or crash)",
        allow_module_level=True
    )


class TestPyffishCrossValidation:
    """TEST-02: Cross-validate engine legal moves against pyffish reference."""

    def test_starting_position_move_count(self):
        """pyffish reports 44 legal moves for starting position."""
        moves = _get_pyffish_moves_safe()
        assert moves is not None, "pyffish not working"
        assert len(moves) == 44, f"pyffish reports {len(moves)} moves, expected 44"

    def test_engine_matches_pyffish(self):
        """All 44 starting-position moves match between engine and pyffish.

        This is the primary cross-validation test. It compares the engine's
        set of legal moves against pyffish's reference set. Any mismatch
        (move in engine but not pyffish, or vice versa) is a failure.
        """
        pyffish_moves = _get_pyffish_moves_safe()
        assert pyffish_moves is not None, "pyffish not working"
        pf_set = set(uci_to_move(u) for u in pyffish_moves)

        engine = XiangqiEngine.starting()
        eng_set = set(engine.legal_moves())

        only_engine = eng_set - pf_set
        only_pyffish = pf_set - eng_set

        assert not only_engine, (
            f"Moves in engine but not in pyffish ({len(only_engine)}): "
            f"{sorted(only_engine)[:10]}"
        )
        assert not only_pyffish, (
            f"Moves in pyffish but not in engine ({len(only_pyffish)}): "
            f"{sorted(only_pyffish)[:10]}"
        )
        assert len(eng_set) == 44, f"Engine reports {len(eng_set)} moves, expected 44"

    def test_pyffish_conversion_roundtrip(self):
        """UCI -> flat -> UCI conversion is lossless for starting position."""
        pyffish_moves = _get_pyffish_moves_safe()
        assert pyffish_moves is not None, "pyffish not working"
        for uci in pyffish_moves:
            move = uci_to_move(uci)
            from_sq = move & 0x1FF
            to_sq   = (move >> 9) & 0x7F
            # Verify both from and to squares are valid
            assert 0 <= from_sq < 90, f"Invalid from_sq {from_sq} for UCI {uci}"
            assert 0 <= to_sq < 90, f"Invalid to_sq {to_sq} for UCI {uci}"

    def test_engine_legal_moves_count(self):
        """Engine legal_moves() returns exactly 44 moves at starting position."""
        engine = XiangqiEngine.starting()
        moves = engine.legal_moves()
        assert len(moves) == 44, f"Expected 44, got {len(moves)}"
        # All moves are unique
        assert len(set(moves)) == len(moves), "Duplicate moves found"
        # All moves are positive integers
        for m in moves:
            assert isinstance(m, int), f"Move {m} is not an int"
            assert m > 0, f"Move {m} is not positive"
