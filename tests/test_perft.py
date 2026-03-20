"""Perft (performance test) for move generation correctness.

Perft recursively counts all leaf nodes (legal positions) at a given depth
from a starting position. Reference values are CPW-verified via Fairy-Stockfish.

CRITICAL: REQUIREMENTS.md contains incorrect perft numbers for depth 2 and 3.
Always use CPW reference values below.

Reference (CPW / Fairy-Stockfish):
  depth 1: 44   (nodes at depth 1, after 1 half-move)
  depth 2: 1,920 (nodes at depth 2, after 2 half-moves)
  depth 3: 79,666 (nodes at depth 3, after 3 half-moves)
  depth 4: 3,290,240 (CPW verified but slow for unit tests)

Source: https://www.chessprogramming.org/Chinese_Chess_Perft_Results
        Fairy-Stockfish CI perft.sh
"""

import pytest

from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.engine.legal import generate_legal_moves, is_in_check
from src.xiangqi.engine.types import rc_to_sq, encode_move


# CPW-verified reference values (CORRECT -- use these)
CPW_PERFT = {
    1: 44,
    2: 1920,
    3: 79666,
    4: 3_290_240,
}

# CPW-verified perft divide at depth 1 (each key = (fr, fc, tr, tc), value = subtree size at depth 2)
CPW_PERFT_DIVIDE = {
    (7, 1, 3, 1): 40,  (7, 7, 3, 7): 40,
    (7, 1, 4, 1): 41,  (7, 7, 4, 7): 41,
    (6, 0, 5, 0): 44,  (7, 1, 5, 1): 42,
    (6, 2, 5, 2): 44,  (6, 4, 5, 4): 44,
    (6, 6, 5, 6): 44,  (7, 7, 5, 7): 42,
    (6, 8, 5, 8): 44,  (7, 1, 6, 1): 43,
    (7, 7, 6, 7): 43,  (7, 1, 7, 0): 45,
    (9, 0, 7, 0): 44,  (9, 1, 7, 0): 43,
    (9, 2, 7, 0): 44,  (7, 1, 7, 2): 45,
    (7, 7, 7, 2): 45,  (9, 1, 7, 2): 43,
    (7, 1, 7, 3): 45,  (7, 7, 7, 3): 45,
    (7, 1, 7, 4): 45,  (7, 7, 7, 4): 45,
    (9, 2, 7, 4): 44,  (9, 6, 7, 4): 44,
    (7, 1, 7, 5): 45,  (7, 7, 7, 5): 45,
    (7, 1, 7, 6): 45,  (7, 7, 7, 6): 45,
    (9, 7, 7, 6): 43,  (7, 7, 7, 8): 45,
    (9, 6, 7, 8): 44,  (9, 7, 7, 8): 43,
    (9, 8, 7, 8): 44,  (9, 0, 8, 0): 44,
    (7, 1, 8, 1): 45,  (9, 3, 8, 4): 44,
    (9, 4, 8, 4): 44,  (9, 5, 8, 4): 44,
    (7, 7, 8, 7): 45,  (9, 8, 8, 8): 44,
    (7, 1, 0, 1): 41,  (7, 7, 0, 7): 41,
}

# REQUIREMENTS.md values (INCORRECT -- for reference only, do not assert against)
REQUIREMENTS_PERFT = {
    1: 44,
    2: 1916,   # WRONG -- correct is 1,920
    3: 72987,  # WRONG -- correct is 79,666
}


def _perft(state: XiangqiState, depth: int) -> int:
    """Recursively count all leaf nodes at given depth from position.

    depth=0: return 1 (current position counts as a leaf)
    depth>0: sum perft(child) for all legal moves
    """
    if depth == 0:
        return 1
    moves = generate_legal_moves(state)
    if depth == 1:
        return len(moves)
    total = 0
    for move in moves:
        snap = state.copy()
        _apply_move(snap, move)
        total += _perft(snap, depth - 1)
    return total


def _apply_move(state: XiangqiState, move: int) -> int:
    """Minimal apply_move for perft (no Zobrist update needed for perft correctness)."""
    from src.xiangqi.engine.types import sq_to_rc
    from_sq = move & 0x1FF
    to_sq = (move >> 9) & 0x7F
    fr, fc = sq_to_rc(from_sq)
    tr, tc = sq_to_rc(to_sq)
    piece = int(state.board[fr, fc])
    captured = int(state.board[tr, tc])
    state.board[tr, tc] = state.board[fr, fc]
    state.board[fr, fc] = 0
    if abs(piece) == 1:
        state.king_positions[state.turn] = to_sq
    if captured != 0 and abs(captured) == 1:
        # Enemy general was captured - remove from king_positions
        enemy = -state.turn
        state.king_positions.pop(enemy, None)
    state.turn *= -1
    return captured


class TestPerftStartingPosition:
    """Verify move generation against CPW/Fairy-Stockfish reference values."""

    def test_perft_depth_1(self):
        """Depth 1: all legal moves from starting position = 44."""
        state = XiangqiState.starting()
        count = _perft(state, depth=1)
        assert count == CPW_PERFT[1], f"perft(1): expected {CPW_PERFT[1]}, got {count}"

    def test_perft_depth_2(self):
        """Depth 2: all nodes at depth 2 = 1,920 (CPW verified; NOT 1,916 from REQUIREMENTS.md)."""
        state = XiangqiState.starting()
        count = _perft(state, depth=2)
        assert count == CPW_PERFT[2], f"perft(2): expected {CPW_PERFT[2]}, got {count}"

    def test_perft_depth_3(self):
        """Depth 3: all nodes at depth 3 = 79,666 (CPW verified; NOT 72,987 from REQUIREMENTS.md).

        This is the critical gate: most move generation bugs appear by depth 3.
        The ~6,679 node gap vs REQUIREMENTS.md (72,987) proves REQUIREMENTS.md is wrong.
        """
        state = XiangqiState.starting()
        count = _perft(state, depth=3)
        assert count == CPW_PERFT[3], f"perft(3): expected {CPW_PERFT[3]}, got {count}"

    def test_perft_depth_4_reference(self):
        """Depth 4: 3,290,240 (CPW verified). Run only as a reference; too slow for CI."""
        state = XiangqiState.starting()
        count = _perft(state, depth=4)
        assert count == CPW_PERFT[4], f"perft(4): expected {CPW_PERFT[4]}, got {count}"

    def test_requirements_md_values_fail(self):
        """Prove REQUIREMENTS.md values are wrong by showing they do NOT match CPW.

        This test documents the discrepancy. If REQUIREMENTS.md is ever corrected,
        this test should be removed or updated.
        """
        state = XiangqiState.starting()
        count2 = _perft(state, depth=2)
        count3 = _perft(state, depth=3)
        # REQUIREMENTS.md says 1,916 but CPW is 1,920
        assert count2 != REQUIREMENTS_PERFT[2], "Should not match incorrect REQUIREMENTS value"
        # REQUIREMENTS.md says 72,987 but CPW is 79,666
        assert count3 != REQUIREMENTS_PERFT[3], "Should not match incorrect REQUIREMENTS value"
        # Must match CPW
        assert count2 == CPW_PERFT[2]
        assert count3 == CPW_PERFT[3]


class TestPerftDivide:
    """perft_divide: break down depth-1 moves to identify which move leads to wrong subtree counts.

    This is the standard Xiangqi debugging technique. If perft(n) fails but perft(n-1) passes,
    divide isolates the buggy move.
    """

    def test_perft_divide_depth_1(self):
        """Return per-move subtree counts at depth 2 as a diagnostic.

        The sum of all depth-2 per-move subtrees must equal perft(2) = 1,920.
        Any move whose subtree sum != expected reveals a bug.
        """
        state = XiangqiState.starting()
        moves = generate_legal_moves(state)
        total = 0
        move_counts = {}
        for move in moves:
            snap = state.copy()
            _apply_move(snap, move)
            sub_count = _perft(snap, depth=1)  # depth 1 from child = depth 2 from root
            move_counts[move] = sub_count
            total += sub_count
        assert total == CPW_PERFT[2], f"Divide sum {total} != {CPW_PERFT[2]}"
        # All individual move counts should be > 0
        for move, cnt in move_counts.items():
            assert cnt > 0, f"Move {move} has 0 nodes -- indicates illegal move included"
        # Per-child CPW reference assertions: each move's subtree must match the CPW value
        for move, cnt in move_counts.items():
            from_sq = move & 0x1FF
            to_sq = (move >> 9) & 0x7F
            fr, fc = rc_to_sq(from_sq) if False else (from_sq // 9, from_sq % 9)
            tr, tc = rc_to_sq(to_sq) if False else (to_sq // 9, to_sq % 9)
            # Actually decode correctly using sq_to_rc
            fr = from_sq // 9
            fc = from_sq % 9
            tr = to_sq // 9
            tc = to_sq % 9
            expected = CPW_PERFT_DIVIDE.get((fr, fc, tr, tc))
            if expected is not None:
                assert cnt == expected, (
                    f"Move ({fr},{fc})->({tr},{tc}): expected {expected}, got {cnt}"
                )


class TestPerftEdgeCases:
    """Perft on non-standard positions to catch piece-specific bugs."""

    def test_perft_trivial_position(self):
        """Chariot and general vs bare opposing general: chariot has 6 moves, general has 3 moves."""
        from src.xiangqi.engine.types import Piece, rc_to_sq
        import numpy as np
        board = np.zeros((10, 9), dtype=np.int8)
        board[7, 4] = Piece.R_SHUAI
        board[0, 4] = Piece.B_JIANG
        board[5, 4] = Piece.R_CHE  # chariot at (5,4)
        state = XiangqiState(
            board=board, turn=+1,
            move_history=[], halfmove_clock=0,
            zobrist_hash_history=[0],
            king_positions={+1: rc_to_sq(7, 4), -1: rc_to_sq(0, 4)},
        )
        # Chariot: 5 upward moves + 1 capture of black general = 6 moves
        # General: 3 moves (to 8,4; 7,3; 7,5)
        # Horizontal chariot moves blocked by flying general rule
        moves = generate_legal_moves(state)
        assert len(moves) == 9  # 6 chariot + 3 general = 9 legal moves
        total = _perft(state, depth=1)
        assert total == 9

    def test_no_illegal_moves_included(self):
        """Verify perft counts at each depth match CPW reference.

        If the move generator includes illegal moves, subtree sizes become inconsistent.
        """
        state = XiangqiState.starting()
        d1 = _perft(state, depth=1)
        d2 = _perft(state, depth=2)
        # Must match CPW reference
        assert d2 == CPW_PERFT[2]
        assert d1 == CPW_PERFT[1]
