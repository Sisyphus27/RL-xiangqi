"""Tests for PieceItem — color, character, size, position."""

import pytest
from src.xiangqi.engine.types import Piece
from src.xiangqi.ui.board_items import PieceItem
from src.xiangqi.ui.constants import RED_FILL, BLACK_FILL, CELL_RATIO


@pytest.fixture
def piece_red():
    """Red shuai (general) at row 9, col 4, cell=50.0."""
    return PieceItem(row=9, col=4, piece_value=int(Piece.R_SHUAI), cell=50.0)


@pytest.fixture
def piece_black():
    """Black jiang (general) at row 0, col 4, cell=50.0."""
    return PieceItem(row=0, col=4, piece_value=int(Piece.B_JIANG), cell=50.0)


class TestPieceColor:
    """Fill color tests — red pieces vs black pieces."""

    def test_red_piece_fill_color(self, piece_red):
        assert piece_red.brush().color().name().upper() == "#CC2200"

    def test_black_piece_fill_color(self, piece_black):
        assert piece_black.brush().color().name().upper() == "#1A1A1A"

    def test_all_red_pieces_positive_value(self, piece_red):
        """Red pieces have positive piece values."""
        assert piece_red._piece_value > 0

    def test_all_black_pieces_negative_value(self, piece_black):
        """Black pieces have negative piece values."""
        assert piece_black._piece_value < 0


class TestPieceCharacter:
    """Chinese character tests — all 14 piece types."""

    def test_red_piece_character(self, piece_red):
        assert piece_red._char == "帅"

    def test_black_piece_character(self, piece_black):
        assert piece_black._char == "将"

    def test_all_piece_characters(self):
        """Every piece type maps to correct Chinese character."""
        test_cases = [
            (+1, "帅"),
            (+2, "仕"),
            (+3, "相"),
            (+4, "马"),
            (+5, "车"),
            (+6, "炮"),
            (+7, "兵"),
            (-1, "将"),
            (-2, "士"),
            (-3, "象"),
            (-4, "馬"),
            (-5, "車"),
            (-6, "砲"),
            (-7, "卒"),
        ]
        for val, expected_char in test_cases:
            p = PieceItem(row=5, col=4, piece_value=val, cell=40.0)
            assert p._char == expected_char, (
                f"Piece({val}): expected {expected_char!r}, got {p._char!r}"
            )


class TestPieceGeometry:
    """Diameter and position tests."""

    def test_piece_diameter_ratio(self, piece_red):
        """Piece diameter is cell * CELL_RATIO (0.80)."""
        d = piece_red.rect().width()
        expected = 50.0 * CELL_RATIO
        assert abs(d - expected) < 0.001

    def test_piece_position(self, piece_red):
        """Piece top-left in scene coords = (col+0.2, row+0.2) * cell."""
        cell = 50.0
        col, row = 4, 9
        assert abs(piece_red.x() - (col + 0.2) * cell) < 0.001
        assert abs(piece_red.y() - (row + 0.2) * cell) < 0.001

    def test_piece_zvalue(self, piece_red):
        """Pieces render above the board background (z > 0)."""
        assert piece_red.zValue() == 1.0

    def test_piece_row_col_stored(self, piece_red):
        """Row and column are stored on the item."""
        assert piece_red._row == 9
        assert piece_red._col == 4
