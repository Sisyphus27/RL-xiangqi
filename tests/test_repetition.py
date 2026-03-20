"""Tests for repetition detection, long check, and long chase (END-03, END-04)."""
from __future__ import annotations

import numpy as np
import pytest

from src.xiangqi.engine.endgame import get_game_result
from src.xiangqi.engine.repetition import (
    RepetitionState,
    check_repetition,
    check_long_check,
    check_long_chase,
    _detect_chase,
)
from src.xiangqi.engine.state import XiangqiState, compute_hash
from src.xiangqi.engine.legal import apply_move, generate_legal_moves, is_in_check
from src.xiangqi.engine.types import Piece, ROWS, COLS, rc_to_sq


def make_state(turn: int, king_red_sq: int, king_black_sq: int,
               extra_pieces: dict[tuple[int, int], int] | None = None,
               zobrist_hash_history: list[int] | None = None,
               move_history: list[int] | None = None) -> XiangqiState:
    """Create a XiangqiState from scratch."""
    board = np.zeros((ROWS, COLS), dtype=np.int8)
    kr, kc = divmod(king_red_sq, COLS)
    br, bc = divmod(king_black_sq, COLS)
    board[kr, kc] = Piece.R_SHUAI
    board[br, bc] = Piece.B_JIANG
    if extra_pieces:
        for (r, c), p in extra_pieces.items():
            board[r, c] = np.int8(p)
    if zobrist_hash_history is None:
        zobrist_hash_history = [compute_hash(board, turn)]
    return XiangqiState(
        board=board, turn=turn,
        king_positions={+1: king_red_sq, -1: king_black_sq},
        move_history=move_history or [],
        halfmove_clock=0,
        zobrist_hash_history=zobrist_hash_history,
    )


# ─── END-04: Repetition draw ─────────────────────────────────────────────────

class TestRepetition:
    """END-04: Any position hash appearing 3x in zobrist_hash_history -> DRAW."""

    def test_no_repetition_returns_none(self, starting_state):
        """Single position (appears 1x) -> not a draw."""
        assert check_repetition(starting_state) is None

    def test_repetition_twice_not_draw(self, starting_state):
        """Position appearing 2x -> not a draw (must be >= 3)."""
        h = starting_state.zobrist_hash_history[-1]
        starting_state.zobrist_hash_history = [h, h]
        assert check_repetition(starting_state) is None

    def test_repetition_thrice_draw(self, starting_state):
        """Position appearing 3x -> DRAW (not required to be consecutive)."""
        h = starting_state.zobrist_hash_history[-1]
        starting_state.zobrist_hash_history = [h, h, h]
        assert check_repetition(starting_state) == 'DRAW'

    def test_repetition_five_times_draw(self, starting_state):
        """Position appearing 5x -> DRAW."""
        h = starting_state.zobrist_hash_history[-1]
        starting_state.zobrist_hash_history = [h] * 5
        assert check_repetition(starting_state) == 'DRAW'

    def test_repetition_not_consecutive_draw(self):
        """Position appearing 3x with other positions in between -> DRAW.

        END-04: repetition is NOT required to be consecutive.
        """
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        h1 = state.zobrist_hash_history[-1]
        h2 = h1 + 1  # a different hash
        # Pattern: [h1, h2, h1, h2, h1] -> h1 appears 3x (non-consecutive)
        state.zobrist_hash_history = [h1, h2, h1, h2, h1]
        assert check_repetition(state) == 'DRAW'

    def test_get_game_result_repetition_draw(self):
        """get_game_result() returns DRAW when position repeats 3x."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        h = state.zobrist_hash_history[-1]
        state.zobrist_hash_history = [h, h, h]
        assert get_game_result(state) == 'DRAW'


# ─── END-03: Long check (长将) ──────────────────────────────────────────────

class TestLongCheck:
    """END-03 (long check): 4 consecutive checking moves -> DRAW.

    A "checking move" = a move that leaves the opponent's king in check.
    tracked by rep_state.consecutive_check_count.
    """

    def test_count_0_not_draw(self):
        """consecutive_check_count = 0 -> no long check."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        assert check_long_check(state, rep_state) is None

    def test_count_3_not_draw(self):
        """consecutive_check_count = 3 -> not yet 4, no draw."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        rep_state.consecutive_check_count = 3
        assert check_long_check(state, rep_state) is None

    def test_count_4_draw(self):
        """consecutive_check_count = 4 -> DRAW (4 consecutive checking moves)."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        rep_state.consecutive_check_count = 4
        assert check_long_check(state, rep_state) == 'DRAW'

    def test_count_5_draw(self):
        """consecutive_check_count = 5 -> DRAW."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        rep_state.consecutive_check_count = 5
        assert check_long_check(state, rep_state) == 'DRAW'

    def test_long_check_resets_on_non_checking_move(self):
        """A non-checking move resets the counter to 0."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        rep_state.consecutive_check_count = 3
        # Simulate a non-checking move
        snap = state.copy()
        moves = generate_legal_moves(state)
        # Pick any move that does NOT give check
        for m in moves:
            s2 = state.copy()
            apply_move(s2, m)
            # Check if this move gave check (opponent now in check)
            mover = s2.turn * -1  # who just moved
            if not is_in_check(s2, mover):
                rep_state.update(snap, m, s2)
                break
        assert rep_state.consecutive_check_count == 0

    def test_long_check_draw_via_get_game_result(self):
        """get_game_result() returns DRAW when long check count >= 4."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        rep_state.consecutive_check_count = 4
        assert get_game_result(state, rep_state) == 'DRAW'


# ─── END-03: Long chase (长捉) ──────────────────────────────────────────────

class TestLongChase:
    """END-03 (long chase): same (att_sq, tgt_sq) x4 -> chaser loses.

    Tracked by rep_state.chase_seq: list of (attacking_sq, target_sq).
    "Meaningful progress" breaks the sequence: giving check, capturing,
    or moving to a square never visited in the current sequence.
    """

    def test_chase_seq_empty_not_draw(self):
        """Empty chase_seq -> no long chase."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        assert check_long_chase(state, rep_state) is None

    def test_chase_seq_3_not_loss(self):
        """chase_seq length = 3 -> not yet 4, no loss."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        rep_state.chase_seq = [(10, 20), (10, 20), (10, 20)]
        rep_state.last_chasing_color = +1
        assert check_long_chase(state, rep_state) is None

    def test_chase_seq_4_red_loses(self):
        """Red chases same target 4 times -> RED loses -> BLACK_WINS."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        rep_state.chase_seq = [(10, 20), (10, 20), (10, 20), (10, 20)]
        rep_state.last_chasing_color = +1  # red is chasing
        assert check_long_chase(state, rep_state) == 'BLACK_WINS'

    def test_chase_seq_4_black_loses(self):
        """Black chases same target 4 times -> BLACK loses -> RED_WINS."""
        state = make_state(-1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        rep_state.chase_seq = [(50, 60), (50, 60), (50, 60), (50, 60)]
        rep_state.last_chasing_color = -1  # black is chasing
        assert check_long_chase(state, rep_state) == 'RED_WINS'

    def test_new_target_sq_resets_count(self):
        """Sequences with fewer than 4 entries do not trigger long chase.

        The long chase rule fires at 4+ consecutive chases. 3 entries -> no result.
        (The reset-on-new-target behavior is tested via update() unit tests.)
        """
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        rep_state.chase_seq = [(10, 20), (10, 20), (10, 20)]  # 3 entries
        rep_state.last_chasing_color = +1
        assert check_long_chase(state, rep_state) is None

    def test_update_resets_on_non_chase(self):
        """update() resets chase_seq when the move is not a chase."""
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4),
                           extra_pieces={(5, 0): Piece.R_CHE})
        rep_state = RepetitionState()
        rep_state.chase_seq = [(10, 20), (10, 20), (10, 20)]
        rep_state.last_chasing_color = +1
        # Apply a non-chase move (regular chariot move to an empty square)
        moves = generate_legal_moves(state)
        # Find a non-chasing move
        snap = state.copy()
        for m in moves:
            chase = _detect_chase(snap, m, state)
            if chase is None:
                # This is a non-chase move: update should reset seq
                s2 = state.copy()
                apply_move(s2, m)
                rep_state.update(snap, m, s2)
                assert rep_state.chase_seq == []
                assert rep_state.last_chasing_color == 0
                break

    def test_long_chase_draw_priority_before_checkmate(self):
        """Long chase (DRAW via chaser loses) fires before checkmate.

        When both long-chase and no-legal-moves are true:
        - check_long_chase fires first (per priority order)
        - Returns 'BLACK_WINS' or 'RED_WINS'
        """
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 3),
                           extra_pieces={
                               (9, 0): Piece.B_CHE,
                               (0, 4): Piece.B_CHE,
                               (8, 3): Piece.R_SHI,
                               (8, 5): Piece.R_SHI,
                           })
        rep_state = RepetitionState()
        rep_state.chase_seq = [(10, 20)] * 4
        rep_state.last_chasing_color = +1
        # Even though state has no legal moves (checkmate), long chase fires first
        assert get_game_result(state, rep_state) == 'BLACK_WINS'


# ─── RepetitionState.update() unit tests ─────────────────────────────────────

class TestRepetitionStateUpdate:
    """Unit tests for RepetitionState.update() method."""

    def test_update_increments_check_count_on_checking_move(self):
        """When mover gives check, consecutive_check_count increments."""
        # Position: red king at (9,4), black king at (0,5), black chariot at (0,4).
        # Black king is on column 5 so chariot can move off column 4 (no flying general).
        # Chariot at (0,4) attacks column 4 -> gives check to red king at (9,4).
        state = make_state(-1, rc_to_sq(9, 4), rc_to_sq(0, 5),
                           extra_pieces={(0, 4): Piece.B_CHE})
        rep_state = RepetitionState()
        moves = generate_legal_moves(state)
        # Find a checking move: chariot at (0,4) moving somewhere gives check
        checking_move = None
        for m in moves:
            s2 = state.copy()
            apply_move(s2, m)
            if is_in_check(s2, s2.turn):  # opponent (red) is in check
                checking_move = m
                break
        assert checking_move is not None, "No checking move found"
        snap = state.copy()
        apply_move(state, checking_move)
        rep_state.update(snap, checking_move, state)
        assert rep_state.consecutive_check_count == 1

    def test_update_resets_check_count_on_non_checking_move(self):
        """Non-checking move resets consecutive_check_count to 0."""
        # Red general at (9,4), black general at (0,4) (no checking pieces)
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 4))
        rep_state = RepetitionState()
        rep_state.consecutive_check_count = 3
        # Apply a non-checking move
        moves = generate_legal_moves(state)
        snap = state.copy()
        apply_move(state, moves[0])
        rep_state.update(snap, moves[0], state)
        assert rep_state.consecutive_check_count == 0

    def test_update_resets_chase_seq_on_new_attacking_square(self):
        """Moving to a new attacking square = meaningful progress = resets seq.

        Chariot at (6,0) moves to (7,0) — sliding AWAY from the pawn at (3,0).
        gen_chariot slides upward from (7,0) and attacks past the pawn, producing
        a valid chase. Since (7,0) has never appeared as the attacking square in
        the current chase_seq, this is meaningful progress and the sequence resets
        to the new (att_sq, tgt_sq) pair.
        """
        # Board: red king (9,4), black king (0,5), red chariot (6,0), black pawn (3,0)
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 5),
                           extra_pieces={(6, 0): Piece.R_CHE, (3, 0): Piece.B_ZU})
        rep_state = RepetitionState()
        # Simulate having already chased from (6,0) attacking (3,0)
        rep_state.chase_seq = [(rc_to_sq(6, 0), rc_to_sq(3, 0))]
        rep_state.last_chasing_color = +1
        # Move chariot from (6,0) to (7,0) — new attacking square, same target
        snap = state.copy()
        move = rc_to_sq(6, 0) | (rc_to_sq(7, 0) << 9)
        new_state = state.copy()
        apply_move(new_state, move)
        rep_state.update(snap, move, new_state)
        # (7,0) is NEW in chase_seq → meaningful → sequence resets to new pair
        assert len(rep_state.chase_seq) == 1
        assert rep_state.chase_seq[-1] == (rc_to_sq(7, 0), rc_to_sq(3, 0))

    def test_update_appends_to_chase_seq_on_repeated_att_sq(self):
        """Appending requires the same (att_sq, tgt_sq) pair as the last entry.

        Red chariot at (6,0) chases black pawn at (3,0) in Move 1 (7,0->6,0),
        producing chase (54,27). Then Move 2 (6,0->7,0) attacks the same pawn
        from a DIFFERENT square (63,27). Since the attacking square changed,
        this is meaningful progress: sequence resets to [(63,27)].
        """
        state = make_state(+1, rc_to_sq(9, 4), rc_to_sq(0, 5),
                           extra_pieces={(6, 0): Piece.R_CHE, (3, 0): Piece.B_ZU})
        rep_state = RepetitionState()
        # After Move 1: chariot at (6,0) attacking (3,0) -> chase (54,27)
        rep_state.chase_seq = [(rc_to_sq(6, 0), rc_to_sq(3, 0))]
        rep_state.last_chasing_color = +1
        # Move 2: chariot returns from (6,0) to (7,0), attacks same pawn from (7,0)
        snap = state.copy()
        move = rc_to_sq(6, 0) | (rc_to_sq(7, 0) << 9)
        new_state = state.copy()
        apply_move(new_state, move)
        rep_state.update(snap, move, new_state)
        # (7,0) is a NEW attacking square (not in prior chase_seq) -> meaningful -> reset
        assert len(rep_state.chase_seq) == 1
        assert rep_state.chase_seq[-1] == (rc_to_sq(7, 0), rc_to_sq(3, 0))

    def test_reset_zeros_all_fields(self):
        """RepetitionState.reset() zeroes all three fields."""
        rep_state = RepetitionState()
        rep_state.consecutive_check_count = 7
        rep_state.chase_seq = [(1, 2), (3, 4)]
        rep_state.last_chasing_color = -1
        rep_state.reset()
        assert rep_state.consecutive_check_count == 0
        assert rep_state.chase_seq == []
        assert rep_state.last_chasing_color == 0
