"""Tests for pseudo-legal piece move generators (MOVE-01..07).

Each gen_* function is tested in isolation using a controlled board setup.
No king-safety filtering here -- that is tested in test_legal.py.
"""
import numpy as np
import pytest

from src.xiangqi.engine.moves import (
    gen_general, gen_chariot, gen_horse, gen_cannon,
    gen_advisor, gen_elephant, gen_soldier,
    belongs_to, all_pieces_of_color,
)
from src.xiangqi.engine.types import Piece, ROWS, COLS, encode_move, decode_move, rc_to_sq
from src.xiangqi.engine.constants import IN_PALACE


class TestBelongsTo:
    """Sanity-check helper before testing individual pieces."""

    def test_red_piece(self):
        assert belongs_to(+5, +1) is True
        assert belongs_to(+5, -1) is False

    def test_black_piece(self):
        assert belongs_to(-5, -1) is True
        assert belongs_to(-5, +1) is False

    def test_empty(self):
        assert belongs_to(0, +1) is False
        assert belongs_to(0, -1) is False


class TestAllPiecesOfColor:
    """all_pieces_of_color returns correct square indices."""

    def test_starting_position(self):
        from src.xiangqi.engine.state import XiangqiState
        state = XiangqiState.starting()
        red_sq = all_pieces_of_color(state.board, +1)
        assert len(red_sq) == 16  # 7 piece types, 16 total

    def test_empty_board(self, empty_board):
        assert all_pieces_of_color(empty_board, +1) == []


class TestGenChariot:
    """MOVE-03: Chariot (CHE) slides orthogonally, stops on any piece."""

    def test_unblocked_chariot(self):
        """Unblocked chariot at (4,4) reaches all squares in row+col = 17 total."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[4, 4] = Piece.R_CHE
        sq = rc_to_sq(4, 4)
        moves = gen_chariot(board, sq, +1)
        # Up 4 + Down 5 + Left 4 + Right 4 = 17
        assert len(moves) == 17
        for m in moves:
            _, to_sq, _ = decode_move(m)
            tr, tc = divmod(to_sq, 9)
            assert board[tr, tc] == 0

    def test_chariot_blocked_by_own_piece(self):
        """Chariot stops before own piece; own piece is not capturable."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[4, 4] = Piece.R_CHE
        board[4, 6] = Piece.R_CHE  # own piece blocks rightward slide
        sq = rc_to_sq(4, 4)
        moves = gen_chariot(board, sq, +1)
        destinations = {decode_move(m)[1] for m in moves}
        assert rc_to_sq(4, 6) not in destinations

    def test_chariot_captures_enemy(self):
        """Chariot stops AT enemy piece and can capture it."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[4, 4] = Piece.R_CHE
        board[4, 6] = Piece.B_MA  # enemy piece blocking rightward
        sq = rc_to_sq(4, 4)
        moves = gen_chariot(board, sq, +1)
        destinations = {decode_move(m)[1] for m in moves}
        assert rc_to_sq(4, 6) in destinations
        captures = [m for m in moves if decode_move(m)[2]]
        assert rc_to_sq(4, 6) in {decode_move(m)[1] for m in captures}


class TestGenHorse:
    """MOVE-04: Horse (MA) L-shape with leg blocking."""

    def test_unblocked_horse(self):
        """Unblocked horse at (5,5) has 8 destinations."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[5, 5] = Piece.R_MA
        sq = rc_to_sq(5, 5)
        moves = gen_horse(board, sq, +1)
        assert len(moves) == 8

    def test_horse_leg_blocked(self):
        """If leg is blocked, that leg's two destinations are unreachable."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[5, 5] = Piece.R_MA
        board[4, 5] = Piece.R_BING  # leg at (4,5) is blocked
        sq = rc_to_sq(5, 5)
        moves = gen_horse(board, sq, +1)
        destinations = {decode_move(m)[1] for m in moves}
        # Leg at (4,5): destinations would be (3,4) and (3,6) -- both unreachable
        assert rc_to_sq(3, 4) not in destinations
        assert rc_to_sq(3, 6) not in destinations
        assert len(moves) < 8
        assert len(moves) >= 6  # 6 remaining legs still work

    def test_horse_corner_leg_block(self):
        """NumPy negative-index wrap: leg at row-1 wraps to row 9 in 10-row board.

        This was a critical Rule 1 bug. board[-1, c] silently returns board[9, c].
        Bounds check must precede array access.
        """
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[0, 1] = Piece.R_MA  # leg at (-1,1) would wrap without bounds check
        sq = rc_to_sq(0, 1)
        moves = gen_horse(board, sq, +1)
        assert all(0 <= decode_move(m)[1] // 9 for m in moves)

    def test_horse_captures_enemy(self):
        """Horse can capture enemy at valid L-destination."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[5, 5] = Piece.R_MA
        # Leg down=(6,5) empty, dests: (7,4) or (7,6)
        board[7, 4] = Piece.B_PAO  # one valid destination
        sq = rc_to_sq(5, 5)
        moves = gen_horse(board, sq, +1)
        destinations = {decode_move(m)[1] for m in moves}
        assert rc_to_sq(7, 4) in destinations


class TestGenCannon:
    """MOVE-05: Cannon (PAO) slides, needs exactly 1 screen to capture."""

    def test_unblocked_cannon(self):
        """Unblocked cannon slides on empty squares (no captures)."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[4, 4] = Piece.R_PAO
        sq = rc_to_sq(4, 4)
        moves = gen_cannon(board, sq, +1)
        # Up 4 + Down 5 + Left 4 + Right 4 = 17 non-capture slides
        assert len(moves) == 17
        assert all(not decode_move(m)[2] for m in moves)

    def test_cannon_capture_requires_screen(self):
        """Cannon can capture only when exactly 1 piece between."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[4, 4] = Piece.R_PAO
        board[4, 2] = Piece.B_ZU   # 1 screen at col 2
        board[4, 0] = Piece.B_ZU   # capture target at col 0 (2nd piece)
        sq = rc_to_sq(4, 4)
        moves = gen_cannon(board, sq, +1)
        dests_with_caps = {decode_move(m)[1] for m in moves if decode_move(m)[2]}
        assert rc_to_sq(4, 0) in dests_with_caps
        assert rc_to_sq(4, 2) not in dests_with_caps  # cannot capture screen itself

    def test_cannon_no_capture_without_screen(self):
        """Cannon cannot capture when enemy is the first piece (zero-screen)."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[4, 4] = Piece.R_PAO
        board[4, 0] = Piece.B_ZU  # enemy at col 0: no screen between
        sq = rc_to_sq(4, 4)
        moves = gen_cannon(board, sq, +1)
        capture_moves = [m for m in moves if decode_move(m)[2]]
        assert rc_to_sq(4, 0) not in {decode_move(m)[1] for m in capture_moves}


class TestGenGeneral:
    """MOVE-01: General (SHUAI/JIANG) moves 1 orthogonal step within palace."""

    def test_red_general_palace_moves(self):
        """Red general at (8,4) has 4 valid palace moves."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[8, 4] = Piece.R_SHUAI
        sq = rc_to_sq(8, 4)
        moves = gen_general(board, sq, +1)
        # Palace rows 7-9, cols 3-5. From (8,4):
        # Up=(7,4)✓ Down=(9,4)✓ Left=(8,3)✓ Right=(8,5)✓ → 4 moves
        assert len(moves) == 4

    def test_general_blocked_by_enemy(self):
        """General can capture enemy in adjacent palace square."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[8, 4] = Piece.R_SHUAI
        board[7, 4] = Piece.B_JIANG  # enemy in adjacent palace square
        sq = rc_to_sq(8, 4)
        moves = gen_general(board, sq, +1)
        destinations = {decode_move(m)[1] for m in moves}
        assert rc_to_sq(7, 4) in destinations
        captures = [m for m in moves if decode_move(m)[2]]
        assert len(captures) == 1

    def test_general_blocked_by_own_piece(self):
        """General cannot move to square occupied by own piece."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[8, 4] = Piece.R_SHUAI
        board[7, 4] = Piece.R_SHI  # own piece blocks upward move
        sq = rc_to_sq(8, 4)
        moves = gen_general(board, sq, +1)
        destinations = {decode_move(m)[1] for m in moves}
        assert rc_to_sq(7, 4) not in destinations

    def test_general_outside_palace_rejected(self):
        """General cannot step outside the palace."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[7, 4] = Piece.R_SHUAI  # at palace boundary row 7
        sq = rc_to_sq(7, 4)
        moves = gen_general(board, sq, +1)
        for m in moves:
            _, to_sq, _ = decode_move(m)
            tr, tc = divmod(to_sq, 9)
            assert IN_PALACE[tr, tc]


class TestGenAdvisor:
    """MOVE-02: Advisor (SHI) moves 1 diagonal step within palace."""

    def test_red_advisor_palace_moves(self):
        """Red advisor at (8,4) has 4 palace destinations."""
        # Red palace: rows 7-9, cols 3-5. Only (8,4) has all 4 diagonals in palace.
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[8, 4] = Piece.R_SHI
        sq = rc_to_sq(8, 4)
        moves = gen_advisor(board, sq, +1)
        assert len(moves) == 4

    def test_advisor_outside_palace_rejected(self):
        """Advisor cannot move outside the palace."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[6, 4] = Piece.R_SHI  # row 6 is outside palace
        sq = rc_to_sq(6, 4)
        moves = gen_advisor(board, sq, +1)
        for m in moves:
            _, to_sq, _ = decode_move(m)
            tr, tc = divmod(to_sq, 9)
            assert IN_PALACE[tr, tc]


class TestGenElephant:
    """MOVE-06: Elephant (XIANG) diagonal 2-step, blocked by eye, cannot cross river."""

    def test_unblocked_elephant(self):
        """Unblocked red elephant at (2,2) has 4 destinations (all in rows 0-4)."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[2, 2] = Piece.R_XIANG
        sq = rc_to_sq(2, 2)
        moves = gen_elephant(board, sq, +1)
        assert len(moves) == 4

    def test_elephant_eye_blocked(self):
        """Elephant cannot move if eye (midpoint) is occupied."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[2, 2] = Piece.R_XIANG
        board[1, 1] = Piece.R_BING  # eye blocked for diagonal to (0,0)
        sq = rc_to_sq(2, 2)
        moves = gen_elephant(board, sq, +1)
        destinations = {decode_move(m)[1] for m in moves}
        assert rc_to_sq(0, 0) not in destinations  # blocked diagonal
        assert len(moves) == 3

    def test_elephant_cannot_cross_river(self):
        """Red elephant destinations must all be rows 0-4 (own half)."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[3, 4] = Piece.R_XIANG  # row 3 is in black home (rows 0-4)
        sq = rc_to_sq(3, 4)
        moves = gen_elephant(board, sq, +1)
        for m in moves:
            _, to_sq, _ = decode_move(m)
            tr, tc = divmod(to_sq, 9)
            assert 0 <= tr <= 4  # red elephant stays on rows 0-4

    def test_elephant_can_capture_on_own_side(self):
        """Elephant can capture enemy piece on its own half."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[2, 2] = Piece.R_XIANG
        board[0, 0] = Piece.B_ZU  # enemy at diagonal destination (0,0)
        sq = rc_to_sq(2, 2)
        moves = gen_elephant(board, sq, +1)
        destinations = {decode_move(m)[1] for m in moves}
        assert rc_to_sq(0, 0) in destinations
        captures = [m for m in moves if decode_move(m)[2]]
        assert len(captures) == 1


class TestGenSoldier:
    """MOVE-07: Soldier (BING/ZU) advances forward; sideways after crossing river."""

    def test_red_soldier_pre_river(self):
        """Red soldier at row 6 (red home) moves only forward."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[6, 3] = Piece.R_BING
        sq = rc_to_sq(6, 3)
        moves = gen_soldier(board, sq, +1)
        # River between rows 4 and 5. Red home = rows 5-9.
        # Red soldier at row 6: fr=6, crossed = (1==+1 and 6<=4) = False → forward only
        assert len(moves) == 1
        assert decode_move(moves[0])[1] == rc_to_sq(7, 3)

    def test_red_soldier_crossed_river(self):
        """Red soldier at row 3 (across river) moves forward + sideways."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[3, 3] = Piece.R_BING
        sq = rc_to_sq(3, 3)
        moves = gen_soldier(board, sq, +1)
        # Red soldier at row 3: fr=3, crossed = (1==+1 and 3<=4) = True → forward + sideways
        assert len(moves) == 3
        destinations = {decode_move(m)[1] for m in moves}
        assert rc_to_sq(4, 3) in destinations   # forward
        assert rc_to_sq(3, 2) in destinations   # left
        assert rc_to_sq(3, 4) in destinations   # right

    def test_black_soldier_pre_river(self):
        """Black soldier at row 3 (black home) moves only forward."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[3, 3] = Piece.B_ZU
        sq = rc_to_sq(3, 3)
        moves = gen_soldier(board, sq, -1)
        # Black home = rows 0-4. Black soldier at row 3: fr=3.
        # crossed = (-1==+1 and 3>=5) or (+1==+1 and 3<=4) = True → wrongly says crossed
        # FIXED: crossed = (color==+1 and fr<=4) or (color==-1 and fr>=5)
        # Black: (-1==+1 and 3<=4) or (-1==-1 and 3>=5) = False → not crossed → forward only
        assert len(moves) == 1
        assert decode_move(moves[0])[1] == rc_to_sq(2, 3)

    def test_black_soldier_crossed_river(self):
        """Black soldier at row 6 (across river) moves forward + sideways."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[6, 3] = Piece.B_ZU
        sq = rc_to_sq(6, 3)
        moves = gen_soldier(board, sq, -1)
        # Black soldier at row 6: crossed = (-1==-1 and 6>=5) = True → forward + sideways
        assert len(moves) == 3
        destinations = {decode_move(m)[1] for m in moves}
        assert rc_to_sq(5, 3) in destinations   # forward
        assert rc_to_sq(6, 2) in destinations   # left
        assert rc_to_sq(6, 4) in destinations   # right

    def test_soldier_captures_enemy(self):
        """Soldier can capture enemy in front."""
        board = np.zeros((ROWS, COLS), dtype=np.int8)
        board[6, 3] = Piece.R_BING
        board[7, 3] = Piece.B_ZU  # enemy in front
        sq = rc_to_sq(6, 3)
        moves = gen_soldier(board, sq, +1)
        captures = [m for m in moves if decode_move(m)[2]]
        assert len(captures) == 1
        assert decode_move(captures[0])[1] == rc_to_sq(7, 3)


class TestMoveEncoding:
    """Sanity check that encode/decode is consistent."""

    def test_encode_decode_roundtrip(self):
        from_sq = rc_to_sq(9, 4)
        to_sq = rc_to_sq(8, 4)
        m = encode_move(from_sq, to_sq, is_capture=False)
        f2, t2, cap = decode_move(m)
        assert f2 == from_sq
        assert t2 == to_sq
        assert cap == 0

    def test_encode_capture_flag(self):
        from_sq = rc_to_sq(9, 4)
        to_sq = rc_to_sq(8, 4)
        m_capture = encode_move(from_sq, to_sq, is_capture=True)
        m_nocap = encode_move(from_sq, to_sq, is_capture=False)
        assert m_capture != m_nocap
