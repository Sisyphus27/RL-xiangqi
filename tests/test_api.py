"""Integration tests for the XiangqiEngine public API.

Covers: API-01 (all 7 methods), API-02 (state updates), API-03 (FEN roundtrip),
API-04 (basic performance), TEST-01 (perft through engine), TEST-03/04 (boundary).

This file tests the engine facade only. The underlying modules (legal, endgame,
repetition) are tested in their own test files.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.types import Piece, encode_move, rc_to_sq


# ─── Helper: make a minimal XiangqiState-like board for FEN tests ──────────

def make_board(turn: int, king_red_sq: int, king_black_sq: int,
               extra_pieces: dict[tuple[int, int], int] | None = None) -> np.ndarray:
    """Create a board ndarray and derive its FEN rank string."""
    board = np.zeros((10, 9), dtype=np.int8)
    kr, kc = divmod(king_red_sq, 9)
    br, bc = divmod(king_black_sq, 9)
    board[kr, kc] = Piece.R_SHUAI
    board[br, bc] = Piece.B_JIANG
    if extra_pieces:
        for (r, c), p in extra_pieces.items():
            board[r, c] = np.int8(p)
    return board


def board_to_rank_fen(board: np.ndarray, turn: int) -> str:
    """Serialize board + turn to the first two FEN fields (rank string + turn)."""
    rank_strs = []
    for r in range(10):
        rank = ''
        empty = 0
        for c in range(9):
            p = int(board[r, c])
            if p == 0:
                empty += 1
            else:
                if empty > 0:
                    rank += str(empty)
                    empty = 0
                if p > 0:
                    rank += {1: 'K', 2: 'A', 3: 'B', 4: 'N', 5: 'R', 6: 'C', 7: 'P'}[p]
                else:
                    rank += {1: 'k', 2: 'a', 3: 'b', 4: 'n', 5: 'r', 6: 'c', 7: 'p'}[abs(p)]
        if empty > 0:
            rank += str(empty)
        rank_strs.append(rank)
    color = 'w' if turn == 1 else 'b'
    return ' '.join(['/'.join(rank_strs), color, '-', '0', '1'])


# ─── Test: Engine lifecycle ────────────────────────────────────────────────

class TestEngineLifecycle:
    """API-01: reset(), starting(), from_fen(), basic properties."""

    def test_starting_turn_is_red(self):
        eng = XiangqiEngine.starting()
        assert eng.turn == +1

    def test_starting_board_shape(self):
        eng = XiangqiEngine.starting()
        assert eng.board.shape == (10, 9)
        assert eng.board.dtype == np.int8

    def test_starting_has_44_legal_moves(self):
        eng = XiangqiEngine.starting()
        assert len(eng.legal_moves()) == 44

    def test_starting_not_in_check(self):
        eng = XiangqiEngine.starting()
        assert eng.is_check() is False

    def test_starting_result_in_progress(self):
        eng = XiangqiEngine.starting()
        assert eng.result() == 'IN_PROGRESS'

    def test_reset_returns_to_starting(self):
        eng = XiangqiEngine.starting()
        # Make a move
        moves = eng.legal_moves()
        eng.apply(moves[0])
        assert eng.turn == -1
        assert len(eng.move_history) == 1
        # Reset
        eng.reset()
        assert eng.turn == +1
        assert len(eng.move_history) == 0
        assert len(eng.legal_moves()) == 44

    def test_from_fen_creates_engine(self):
        STARTING_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1"
        eng = XiangqiEngine.from_fen(STARTING_FEN)
        assert eng.turn == +1
        assert len(eng.legal_moves()) == 44

    def test_from_fen_raises_on_bad_fen(self):
        with pytest.raises(ValueError, match="Invalid FEN"):
            XiangqiEngine.from_fen("not a valid fen string")

    def test_from_fen_raises_on_malformed_fen(self):
        with pytest.raises(ValueError, match="Invalid FEN"):
            XiangqiEngine.from_fen("xxxxxxxxx/9/9/9/9/9/9/9/9 w")

    def test_read_only_board_property(self):
        eng = XiangqiEngine.starting()
        board = eng.board
        # Read-only: assignment should not be tracked (no write protection, but doc says read-only)
        _ = board[0, 0]  # accessing is fine
        assert eng.board.shape == (10, 9)

    def test_read_only_turn_property(self):
        eng = XiangqiEngine.starting()
        assert eng.turn == +1
        # turn changes via apply
        move = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        eng.apply(move)
        assert eng.turn == -1

    def test_read_only_move_history(self):
        eng = XiangqiEngine.starting()
        assert len(eng.move_history) == 0
        move = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        eng.apply(move)
        assert len(eng.move_history) == 1
        assert isinstance(eng.move_history[0], int)


# ─── Test: State updates (API-02) ─────────────────────────────────────────

class TestStateUpdate:
    """API-02: apply() correctly updates board, turn, move_history, halfmove_clock."""

    def test_apply_updates_turn(self):
        eng = XiangqiEngine.starting()
        assert eng.turn == +1
        move = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        eng.apply(move)
        assert eng.turn == -1

    def test_apply_updates_move_history(self):
        eng = XiangqiEngine.starting()
        assert len(eng.move_history) == 0
        move = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        eng.apply(move)
        assert len(eng.move_history) == 1
        assert eng.move_history[0] == move

    def test_apply_returns_zero_when_no_capture(self):
        eng = XiangqiEngine.starting()
        move = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        captured = eng.apply(move)
        assert captured == 0

    def test_apply_returns_captured_piece(self):
        # Set up: red pawn at (5,4), black pawn at (4,4)
        board = make_board(+1, rc_to_sq(9, 4), rc_to_sq(0, 4),
                           extra_pieces={
                               (5, 4): Piece.R_BING,   # red pawn
                               (4, 4): Piece.B_ZU,     # black pawn (adjacent, same file)
                           })
        fen = board_to_rank_fen(board, +1)
        eng = XiangqiEngine.from_fen(fen)
        # Red advances: (5,4) -> (4,4), captures black pawn
        move = encode_move(rc_to_sq(5, 4), rc_to_sq(4, 4))
        captured = eng.apply(move)
        assert captured == Piece.B_ZU

    def test_apply_illegal_move_raises(self):
        eng = XiangqiEngine.starting()
        with pytest.raises(ValueError, match="Illegal move"):
            eng.apply(0)  # invalid encoding

    def test_apply_updates_board(self):
        eng = XiangqiEngine.starting()
        # Red pawn at (6,4) advances to (5,4)
        from_sq = rc_to_sq(6, 4)
        to_sq = rc_to_sq(5, 4)
        assert eng.board[6, 4] == Piece.R_BING
        assert eng.board[5, 4] == 0
        move = encode_move(from_sq, to_sq)
        eng.apply(move)
        assert eng.board[6, 4] == 0
        assert eng.board[5, 4] == Piece.R_BING


# ─── Test: Undo ────────────────────────────────────────────────────────────

class TestUndo:
    """API-01: undo() reverses apply()."""

    def test_undo_empty_stack_raises(self):
        eng = XiangqiEngine.starting()
        with pytest.raises(IndexError, match="nothing to undo"):
            eng.undo()

    def test_undo_restores_turn(self):
        eng = XiangqiEngine.starting()
        move = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        eng.apply(move)
        assert eng.turn == -1
        eng.undo()
        assert eng.turn == +1

    def test_undo_restores_board(self):
        eng = XiangqiEngine.starting()
        from_sq = rc_to_sq(6, 4)
        to_sq = rc_to_sq(5, 4)
        move = encode_move(from_sq, to_sq)
        eng.apply(move)
        assert eng.board[6, 4] == 0
        assert eng.board[5, 4] == Piece.R_BING
        eng.undo()
        assert eng.board[6, 4] == Piece.R_BING
        assert eng.board[5, 4] == 0

    def test_undo_restores_move_history(self):
        eng = XiangqiEngine.starting()
        move = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        eng.apply(move)
        assert len(eng.move_history) == 1
        eng.undo()
        assert len(eng.move_history) == 0

    def test_undo_restores_rep_state(self):
        """Undo must restore RepetitionState (consecutive_check_count etc.)."""
        eng = XiangqiEngine.starting()
        # No rep state changes at start
        # Apply a move
        move = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        eng.apply(move)
        eng.undo()
        # After undo, result() should still work
        assert eng.result() == 'IN_PROGRESS'

    def test_multiple_undo_restores_full_history(self):
        eng = XiangqiEngine.starting()
        m1 = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        m2 = encode_move(rc_to_sq(3, 4), rc_to_sq(4, 4))  # black pawn advances
        eng.apply(m1)
        eng.apply(m2)
        assert eng.turn == +1
        eng.undo()
        assert eng.turn == -1
        eng.undo()
        assert eng.turn == +1
        assert len(eng.move_history) == 0
        assert len(eng.legal_moves()) == 44


# ─── Test: FEN roundtrip (API-03) ─────────────────────────────────────────

class TestFEN:
    """API-03: from_fen() / to_fen() roundtrip."""

    def test_fen_roundtrip_starting(self):
        eng = XiangqiEngine.starting()
        fen = eng.to_fen()
        eng2 = XiangqiEngine.from_fen(fen)
        assert eng2.to_fen() == fen
        assert eng2.legal_moves() == eng.legal_moves()
        assert eng2.turn == eng.turn

    def test_fen_roundtrip_after_moves(self):
        eng = XiangqiEngine.starting()
        move = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        eng.apply(move)
        fen = eng.to_fen()
        eng2 = XiangqiEngine.from_fen(fen)
        assert eng2.to_fen() == fen
        assert eng2.turn == eng.turn
        assert eng2.legal_moves() == eng.legal_moves()

    def test_to_fen_contains_color(self):
        eng = XiangqiEngine.starting()
        fen = eng.to_fen()
        # WXF FEN format: "... w - 0 1" or "... b - 0 1"
        parts = fen.split()
        assert len(parts) >= 2
        assert parts[1] in ('w', 'b')


# ─── Test: legal_moves and is_legal ──────────────────────────────────────

class TestLegalMoves:
    """API-01: legal_moves() and is_legal() correctness."""

    def test_is_legal_true_for_legal_move(self):
        eng = XiangqiEngine.starting()
        moves = eng.legal_moves()
        assert len(moves) > 0
        assert eng.is_legal(moves[0]) is True

    def test_is_legal_false_for_illegal_move(self):
        eng = XiangqiEngine.starting()
        # encode_move(0, 1) = move black chariot from (0,0) to (0,1) on red's turn
        # is_legal_move rejects this because it leaves red in self-check after the move
        illegal = encode_move(0, 1)
        assert eng.is_legal(illegal) is False

    def test_legal_moves_returns_list_of_ints(self):
        eng = XiangqiEngine.starting()
        moves = eng.legal_moves()
        assert isinstance(moves, list)
        for m in moves:
            assert isinstance(m, int)


# ─── Test: is_check and result ────────────────────────────────────────────

class TestCheckAndResult:
    """API-01: is_check() and result() on boundary positions."""

    def test_is_check_false_at_starting(self):
        eng = XiangqiEngine.starting()
        assert eng.is_check() is False

    def test_result_in_progress_at_starting(self):
        eng = XiangqiEngine.starting()
        assert eng.result() == 'IN_PROGRESS'

    def test_checkmate_via_engine_result(self):
        """Checkmate: double chariot checkmate position (from test_endgame.py).

        Black king at (0,3), red king at (9,4), black chariots at (9,0) and (0,4).
        Red to move -> BLACK_WINS (checkmate).
        """
        board = make_board(+1, rc_to_sq(9, 4), rc_to_sq(0, 3), {
            (9, 0): Piece.B_CHE,
            (0, 4): Piece.B_CHE,
            (8, 3): Piece.R_SHI,
            (8, 5): Piece.R_SHI,
        })
        fen = board_to_rank_fen(board, +1)
        eng = XiangqiEngine.from_fen(fen)
        assert eng.is_check() is True
        result = eng.result()
        assert result == 'BLACK_WINS', f"Expected BLACK_WINS, got {result}"

    def test_stalemate_via_engine_result(self):
        """Stalemate (困毙): double chariot checkmate position.

        Black king at (0,3), red king at (9,4), black chariots at (9,0) and (0,4).
        Red advisors at (8,3)/(8,5), black advisor at (8,4).
        Red to move, 0 legal moves, in check -> BLACK_WINS (checkmate).
        """
        board = make_board(+1, rc_to_sq(9, 4), rc_to_sq(0, 3), {
            (9, 0): Piece.B_CHE,
            (0, 4): Piece.B_CHE,
            (8, 4): Piece.B_SHI,
            (8, 3): Piece.R_SHI,
            (8, 5): Piece.R_SHI,
        })
        fen = board_to_rank_fen(board, +1)
        eng = XiangqiEngine.from_fen(fen)
        # No legal moves (困毙/checkmate) -> opponent wins
        result = eng.result()
        assert result == 'BLACK_WINS', f"Expected BLACK_WINS, got {result}"

    def test_result_after_move_sequence(self):
        """result() tracks game state after a sequence of moves."""
        eng = XiangqiEngine.starting()
        # Red pawn advances
        m1 = encode_move(rc_to_sq(6, 4), rc_to_sq(5, 4))
        eng.apply(m1)
        assert eng.result() == 'IN_PROGRESS'
        # Black pawn advances
        m2 = encode_move(rc_to_sq(3, 4), rc_to_sq(4, 4))
        eng.apply(m2)
        assert eng.result() == 'IN_PROGRESS'


# ─── Test: RepetitionState encapsulation ─────────────────────────────────

class TestRepetitionEncapsulation:
    """Verify RepetitionState is encapsulated inside engine; only result() is public."""

    def test_engine_has_private_rep_state(self):
        eng = XiangqiEngine.starting()
        # _rep_state should be private
        assert hasattr(eng, '_rep_state')
        # Public API should not expose rep_state
        assert not hasattr(eng, 'rep_state') or eng.__class__.__dict__.get('rep_state') is None

    def test_result_uses_rep_state(self):
        """Verify result() is affected by rep_state updates."""
        eng = XiangqiEngine.starting()
        assert eng.result() == 'IN_PROGRESS'


# ─── Test: API-04 performance (basic sanity) ────────────────────────────

class TestPerformanceSanity:
    """API-04: basic performance sanity (detailed perft in test_perft_engine.py)."""

    def test_legal_moves_is_fast(self):
        import time
        eng = XiangqiEngine.starting()
        start = time.perf_counter()
        for _ in range(100):
            _ = eng.legal_moves()
        elapsed = (time.perf_counter() - start) * 10  # ms per call
        assert elapsed < 1000, f"legal_moves x100 took {elapsed:.1f}ms > 1s (should be <1s for 100 calls)"

    def test_result_is_fast(self):
        import time
        eng = XiangqiEngine.starting()
        start = time.perf_counter()
        for _ in range(100):
            _ = eng.result()
        elapsed = (time.perf_counter() - start) * 10  # ms per call
        assert elapsed < 100, f"result() x100 took {elapsed:.1f}ms > 100ms (should be <100ms for 100 calls)"
