import numpy as np
import pytest
from src.xiangqi.engine.constants import (
    STARTING_FEN,
    IN_PALACE, IN_RIVER, IN_BLACK_HOME, IN_RED_HOME,
    from_fen, to_fen,
)
from src.xiangqi.engine.types import Piece


class TestBoundaryMasks:
    """DATA-05: Palace and home-half boundary masks are correct boolean ndarray masks."""

    def test_palace_mask_shape(self):
        """Palace mask is (10, 9) boolean ndarray."""
        assert IN_PALACE.shape == (10, 9)
        assert IN_PALACE.dtype == bool

    def test_palace_mask_squares(self):
        """DATA-05: Black palace rows 0-2 cols 3-5, red palace rows 7-9 cols 3-5."""
        # Black palace
        assert IN_PALACE[0, 3] and IN_PALACE[0, 4] and IN_PALACE[0, 5]
        assert IN_PALACE[2, 3] and IN_PALACE[2, 4] and IN_PALACE[2, 5]
        assert IN_PALACE[3, 3] == False  # row 3 is not in black palace
        # Red palace
        assert IN_PALACE[7, 3] and IN_PALACE[7, 4] and IN_PALACE[7, 5]
        assert IN_PALACE[9, 3] and IN_PALACE[9, 4] and IN_PALACE[9, 5]
        assert IN_PALACE[6, 3] == False  # row 6 is not in red palace

    def test_river_mask(self):
        """DATA-05: River is rows 4-5, all columns."""
        assert IN_RIVER.shape == (10, 9)
        assert IN_RIVER[4, :].all() and IN_RIVER[5, :].all()
        assert not IN_RIVER[3, :].any() and not IN_RIVER[6, :].any()

    def test_home_half_masks(self):
        """DATA-05: Black home rows 0-4, red home rows 5-9."""
        assert IN_BLACK_HOME.shape == (10, 9)
        assert IN_BLACK_HOME[4, :].all() and IN_BLACK_HOME[5, 0] == False
        assert IN_RED_HOME[5, :].all() and IN_RED_HOME[4, 0] == False


class TestStartingFen:
    """DATA-05: STARTING_FEN parses to correct initial board layout."""

    def test_starting_fen_parsed(self):
        """DATA-05: from_fen(STARTING_FEN) produces correct piece layout."""
        board, turn = from_fen(STARTING_FEN)
        assert board.shape == (10, 9)
        assert board.dtype == np.int8
        assert turn == 1  # red to move

    def test_starting_fen_red_back_rank(self):
        """DATA-05: Red pieces on rank 9 (row 9): CHE CHE, MA MA, XIANG XIANG, SHI SHI, SHUAI."""
        board, _ = from_fen(STARTING_FEN)
        row9 = board[9, :]
        assert row9[0] == Piece.R_CHE
        assert row9[1] == Piece.R_MA
        assert row9[2] == Piece.R_XIANG
        assert row9[3] == Piece.R_SHI
        assert row9[4] == Piece.R_SHUAI
        assert row9[5] == Piece.R_SHI
        assert row9[6] == Piece.R_XIANG
        assert row9[7] == Piece.R_MA
        assert row9[8] == Piece.R_CHE

    def test_starting_fen_black_back_rank(self):
        """DATA-05: Black pieces on rank 0 (row 0)."""
        board, _ = from_fen(STARTING_FEN)
        row0 = board[0, :]
        assert row0[0] == Piece.B_CHE
        assert row0[1] == Piece.B_MA
        assert row0[2] == Piece.B_XIANG
        assert row0[3] == Piece.B_SHI
        assert row0[4] == Piece.B_JIANG
        assert row0[5] == Piece.B_SHI
        assert row0[6] == Piece.B_XIANG
        assert row0[7] == Piece.B_MA
        assert row0[8] == Piece.B_CHE

    def test_starting_fen_pawns(self):
        """DATA-05: 5 red pawns on row 6, 5 black pawns on row 3."""
        board, _ = from_fen(STARTING_FEN)
        # Red pawns row 6 at columns 0, 2, 4, 6, 8
        assert board[6, 0] == Piece.R_BING
        assert board[6, 2] == Piece.R_BING
        assert board[6, 4] == Piece.R_BING
        assert board[6, 6] == Piece.R_BING
        assert board[6, 8] == Piece.R_BING
        # Black pawns row 3 at columns 0, 2, 4, 6, 8
        assert board[3, 0] == Piece.B_ZU
        assert board[3, 2] == Piece.B_ZU
        assert board[3, 4] == Piece.B_ZU
        assert board[3, 6] == Piece.B_ZU
        assert board[3, 8] == Piece.B_ZU

    def test_fen_roundtrip(self):
        """DATA-05: to_fen(from_fen(fen)) == fen (board ranks + color only)."""
        board, turn = from_fen(STARTING_FEN)
        roundtrip = to_fen(board, turn)
        # Compare rank strings and color only
        assert roundtrip.split()[0] == STARTING_FEN.split()[0]
        assert roundtrip.split()[1] == 'w'  # turn preserved
        # Also test a custom FEN
        board2, turn2 = from_fen("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - 0 1")
        assert turn2 == -1
