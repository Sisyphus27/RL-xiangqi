"""Perft benchmarks through the XiangqiEngine public API.

TEST-01: Verifies move generation through engine.apply/undo/legal_moves matches CPW reference.
API-04: Validates performance: legal_moves() < 10ms, result() < 100ms.

Reference values (CPW / Fairy-Stockfish):
  depth 1: 44
  depth 2: 1,920
  depth 3: 79,666

IMPORTANT: This tests the ENGINE API, not direct module calls.
Each perft step uses engine.apply() + engine.undo() to navigate the tree.

Source: https://www.chessprogramming.org/Chinese_Chess_Perft_Results
        Fairy-Stockfish CI perft.sh
"""
from __future__ import annotations

import time
import pytest

from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.types import encode_move, rc_to_sq


# CPW-verified reference values
CPW_PERFT = {1: 44, 2: 1920, 3: 79666}


def _perft(engine: XiangqiEngine, depth: int) -> int:
    """Recursively count leaf nodes at depth D using engine public API.

    Uses apply() + undo() to traverse the move tree.
    After returning from recursion, undo restores the position for the next sibling.

    depth=0: current position is a leaf -> return 1
    depth=1: count all legal moves (without exploring deeper)
    depth>1: for each move: apply, recurse, undo
    """
    if depth == 0:
        return 1
    moves = engine.legal_moves()
    if depth == 1:
        return len(moves)
    total = 0
    for move in moves:
        engine.apply(move)
        total += _perft(engine, depth - 1)
        engine.undo()
    return total


class TestEnginePerft:
    """TEST-01: Verify perft counts through engine API match CPW references."""

    def test_perft_depth_1(self):
        """Depth 1: 44 legal moves from starting position."""
        eng = XiangqiEngine.starting()
        count = _perft(eng, depth=1)
        assert count == CPW_PERFT[1], f"perft(1): expected {CPW_PERFT[1]}, got {count}"

    def test_perft_depth_2(self):
        """Depth 2: 1,920 total nodes."""
        eng = XiangqiEngine.starting()
        count = _perft(eng, depth=2)
        assert count == CPW_PERFT[2], f"perft(2): expected {CPW_PERFT[2]}, got {count}"

    def test_perft_depth_3(self):
        """Depth 3: 79,666 total nodes (CPW verified).

        This is the critical gate: most move-generation bugs surface by depth 3.
        """
        eng = XiangqiEngine.starting()
        count = _perft(eng, depth=3)
        assert count == CPW_PERFT[3], f"perft(3): expected {CPW_PERFT[3]}, got {count}"

    def test_perft_undo_preserves_position(self):
        """After exploring all depth-2 nodes, engine is back at starting position."""
        eng = XiangqiEngine.starting()
        _perft(eng, depth=2)
        # After full perft(2), undo stack should be empty (each apply was undone)
        assert eng.turn == +1
        assert len(eng.move_history) == 0
        assert len(eng.legal_moves()) == 44

    def test_perft_engine_matches_direct_module(self):
        """Verify engine-based perft matches the direct-module perft.

        This cross-check catches bugs in the engine's apply/undo implementation.
        """
        from src.xiangqi.engine.state import XiangqiState
        from src.xiangqi.engine.legal import generate_legal_moves

        # Direct-module perft (uses state.copy())
        def _perft_direct(state, depth):
            if depth == 0:
                return 1
            moves = generate_legal_moves(state)
            if depth == 1:
                return len(moves)
            total = 0
            for move in moves:
                snap = state.copy()
                from src.xiangqi.engine.legal import apply_move as _am
                _am(snap, move)
                total += _perft_direct(snap, depth - 1)
            return total

        direct = _perft_direct(XiangqiState.starting(), depth=2)
        engine_count = _perft(XiangqiEngine.starting(), depth=2)
        assert engine_count == direct, (
            f"Engine perft({2})={engine_count} != direct perft({2})={direct}"
        )


class TestAPI04Performance:
    """API-04: Performance targets: legal_moves < 10ms, result < 100ms."""

    def test_legal_moves_under_10ms(self):
        """legal_moves() must complete in under 10ms on starting position."""
        eng = XiangqiEngine.starting()
        # Warm-up (avoid JIT/compile variance)
        _ = eng.legal_moves()
        # Measure
        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            _ = eng.legal_moves()
        elapsed_ms = (time.perf_counter() - start) * 1000 / iterations
        assert elapsed_ms < 10, (
            f"legal_moves() took {elapsed_ms:.3f}ms > 10ms target. "
            f"100 iterations took {elapsed_ms * iterations:.1f}ms total."
        )

    def test_result_under_100ms(self):
        """result() must complete in under 100ms on starting position."""
        eng = XiangqiEngine.starting()
        # Warm-up
        _ = eng.result()
        # Measure
        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            _ = eng.result()
        elapsed_ms = (time.perf_counter() - start) * 1000 / iterations
        assert elapsed_ms < 100, (
            f"result() took {elapsed_ms:.3f}ms > 100ms target. "
            f"100 iterations took {elapsed_ms * iterations:.1f}ms total."
        )

    def test_apply_is_fast(self):
        """apply() must be fast (no blocking operations)."""
        eng = XiangqiEngine.starting()
        moves = eng.legal_moves()
        # Warm-up
        eng.apply(moves[0])
        eng.undo()
        # Measure single apply+undo cycle
        iterations = 1000
        start = time.perf_counter()
        for move in moves[:min(iterations, len(moves))]:
            eng.apply(move)
            eng.undo()
        elapsed_ms = (time.perf_counter() - start) * 1000 / min(iterations, len(moves))
        assert elapsed_ms < 5, f"apply+undo took {elapsed_ms:.3f}ms > 5ms per call"
