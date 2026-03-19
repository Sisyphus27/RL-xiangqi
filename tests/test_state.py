"""Tests for XiangqiState dataclass and Zobrist hashing (DATA-04)."""
import numpy as np
import pytest

from src.xiangqi.engine.state import XiangqiState, compute_hash, update_hash, _zobrist_piece
from src.xiangqi.engine.types import Piece


class TestXiangqiStateFields:
    """DATA-04: XiangqiState has all required fields with correct types."""

    def test_state_fields_exist(self):
        """DATA-04: All 5 required fields present."""
        state = XiangqiState.starting()
        assert hasattr(state, 'board')
        assert hasattr(state, 'turn')
        assert hasattr(state, 'move_history')
        assert hasattr(state, 'halfmove_clock')
        assert hasattr(state, 'zobrist_hash_history')

    def test_state_field_types(self):
        """DATA-04: Field types are correct."""
        state = XiangqiState.starting()
        assert isinstance(state.board, np.ndarray)
        assert state.board.shape == (10, 9)
        assert state.board.dtype == np.int8
        assert state.turn in (+1, -1)
        assert isinstance(state.move_history, list)
        assert state.halfmove_clock == 0
        assert isinstance(state.zobrist_hash_history, list)

    def test_king_positions_field(self):
        """DATA-04 + researcher recommendation: king_positions dict is present."""
        state = XiangqiState.starting()
        assert hasattr(state, 'king_positions')
        assert isinstance(state.king_positions, dict)
        assert +1 in state.king_positions
        assert -1 in state.king_positions
        # Verify the squares contain the correct kings
        red_sq = state.king_positions[+1]
        black_sq = state.king_positions[-1]
        assert int(state.board.flat[red_sq]) == Piece.R_SHUAI
        assert int(state.board.flat[black_sq]) == Piece.B_JIANG


class TestStateConstruction:
    """DATA-04: State construction from FEN."""

    def test_starting_state(self):
        """DATA-04: XiangqiState.starting() produces correct initial position."""
        state = XiangqiState.starting()
        assert state.turn == 1  # red to move
        # Red back rank row 9
        assert state.board[9, 0] == Piece.R_CHE
        assert state.board[9, 4] == Piece.R_SHUAI
        # Black back rank row 0
        assert state.board[0, 0] == Piece.B_CHE
        assert state.board[0, 4] == Piece.B_JIANG
        # Red pawns row 6
        assert state.board[6, 0] == Piece.R_BING
        # Black pawns row 3
        assert state.board[3, 0] == Piece.B_ZU

    def test_from_fen_default(self):
        """DATA-04: from_fen produces same board as starting()."""
        state1 = XiangqiState.starting()
        state2 = XiangqiState.from_fen(
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1"
        )
        assert state1.board.tolist() == state2.board.tolist()
        assert state1.turn == state2.turn

    def test_from_fen_black_to_move(self):
        """DATA-04: from_fen correctly sets turn from FEN color field."""
        state = XiangqiState.from_fen(
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - 0 1"
        )
        assert state.turn == -1


class TestStateCopy:
    """DATA-04: state.copy() produces independent deep copy."""

    def test_copy_board_independent(self):
        """DATA-04: copy.board is a new array, not a view."""
        state = XiangqiState.starting()
        state2 = state.copy()
        assert state2.board is not state.board
        state2.board[9, 4] = Piece.EMPTY  # modify copy
        assert state.board[9, 4] == Piece.R_SHUAI  # original unchanged

    def test_copy_lists_independent(self):
        """DATA-04: copy.move_history and zobrist_hash_history are new lists."""
        state = XiangqiState.starting()
        state2 = state.copy()
        assert state2.move_history is not state.move_history
        assert state2.zobrist_hash_history is not state.zobrist_hash_history
        state2.move_history.append(99)
        assert 99 not in state.move_history


class TestZobristHashing:
    """DATA-04: Zobrist hash initialization and computation."""

    def test_zobrist_table_shape(self):
        """DATA-04: _zobrist_piece has shape (15, 90) and dtype uint64."""
        assert _zobrist_piece.shape == (15, 90)
        assert _zobrist_piece.dtype == np.uint64

    def test_zobrist_table_deterministic(self):
        """DATA-04: Zobrist table is deterministic (same seed)."""
        # The table is module-level — just verify it's non-zero and stable
        assert _zobrist_piece[7, 0] != 0  # at least one entry is non-zero
        # Re-import should give same value (module caching)
        import importlib
        import src.xiangqi.engine.state as state_mod
        importlib.reload(state_mod)
        assert state_mod._zobrist_piece[7, 0] == _zobrist_piece[7, 0]

    def test_compute_hash_starting_position(self):
        """DATA-04: compute_hash returns a consistent int for starting position."""
        state = XiangqiState.starting()
        h = compute_hash(state.board, state.turn)
        assert isinstance(h, int)
        assert h != 0
        # Hash should match the initial hash in the history
        assert state.zobrist_hash_history[0] == h

    def test_update_hash_changes_hash(self):
        """DATA-04: update_hash produces a different hash after a move."""
        state = XiangqiState.starting()
        old_hash = state.zobrist_hash_history[-1]
        # Simulate moving red horse from b1 (row 9, col 1) to a3 (row 6, col 0)
        from_sq = 9 * 9 + 1   # b1
        to_sq = 6 * 9 + 0     # a3
        piece = int(state.board[9, 1])  # R_MA = 4
        captured = 0
        new_hash = update_hash(old_hash, from_sq, to_sq, piece, captured, -1)
        assert new_hash != old_hash

    def test_zobrist_hash_history_initialized(self):
        """DATA-04: zobrist_hash_history contains exactly one hash at start."""
        state = XiangqiState.starting()
        assert len(state.zobrist_hash_history) == 1
        assert isinstance(state.zobrist_hash_history[0], int)
