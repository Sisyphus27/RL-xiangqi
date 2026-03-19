import numpy as np
import pytest
from src.xiangqi.engine.types import (
    Piece, encode_move, decode_move, rc_to_sq, sq_to_rc, ROWS, COLS, NUM_SQUARES
)


class TestPieceEnum:
    """DATA-02: Piece IntEnum with pinyin names and Chinese __repr__."""

    def test_piece_values(self):
        """DATA-01: 0=empty, +1..+7=red, -1..-7=black."""
        assert Piece.EMPTY == 0
        assert Piece.R_SHUAI == +1
        assert Piece.B_JIANG == -1
        assert Piece.R_SHI == +2
        assert Piece.B_SHI == -2
        assert Piece.R_XIANG == +3
        assert Piece.B_XIANG == -3
        assert Piece.R_MA == +4
        assert Piece.B_MA == -4
        assert Piece.R_CHE == +5
        assert Piece.B_CHE == -5
        assert Piece.R_PAO == +6
        assert Piece.B_PAO == -6
        assert Piece.R_BING == +7
        assert Piece.B_ZU == -7

    def test_piece_enum_repr(self):
        """DATA-02: __repr__ returns Chinese character string."""
        assert repr(Piece.R_SHUAI) == '帅'
        assert repr(Piece.B_JIANG) == '将'
        assert repr(Piece.R_SHI) == '仕'
        assert repr(Piece.R_XIANG) == '相'
        assert repr(Piece.R_MA) == '马'
        assert repr(Piece.R_CHE) == '车'
        assert repr(Piece.R_PAO) == '炮'
        assert repr(Piece.R_BING) == '兵'
        assert repr(Piece.EMPTY) == '　'
        assert repr(Piece.B_ZU) == '卒'
        assert repr(Piece.B_SHI) == '士'
        assert repr(Piece.B_XIANG) == '象'
        assert repr(Piece.B_MA) == '馬'
        assert repr(Piece.B_CHE) == '車'
        assert repr(Piece.B_PAO) == '砲'

    def test_piece_intenum_arithmetic(self):
        """DATA-02: IntEnum arithmetic works (abs, negation)."""
        assert abs(Piece.R_SHUAI) == abs(Piece.B_JIANG) == 1
        assert abs(Piece.R_SHI) == abs(Piece.B_SHI) == 2
        assert abs(Piece.R_XIANG) == abs(Piece.B_XIANG) == 3
        assert abs(Piece.R_MA) == abs(Piece.B_MA) == 4
        assert abs(Piece.R_CHE) == abs(Piece.B_CHE) == 5
        assert abs(Piece.R_PAO) == abs(Piece.B_PAO) == 6
        assert abs(Piece.R_BING) == abs(Piece.B_ZU) == 7
        # Negation gives opposite color
        assert -Piece.R_SHUAI == Piece.B_JIANG
        assert -Piece.R_CHE == Piece.B_CHE
        assert -Piece.R_BING == Piece.B_ZU


class TestMoveEncoding:
    """DATA-03: 16-bit move encoding with encode/decode roundtrip."""

    def test_encode_decode_roundtrip(self):
        """DATA-03: encode/decode roundtrip for all 90x89 non-no-op pairs."""
        for from_sq in range(90):
            for to_sq in range(90):
                if from_sq == to_sq:
                    continue
                for cap in (False, True):
                    m = encode_move(from_sq, to_sq, cap)
                    f, t, c = decode_move(m)
                    assert f == from_sq, f"from_sq mismatch {f} != {from_sq}"
                    assert t == to_sq, f"to_sq mismatch {t} != {to_sq}"
                    assert c == cap, f"is_capture mismatch {c} != {cap}"

    def test_sq_rc_helpers(self):
        """DATA-03: rc_to_sq and sq_to_rc are inverses."""
        for row in range(ROWS):
            for col in range(COLS):
                sq = rc_to_sq(row, col)
                assert 0 <= sq < NUM_SQUARES
                r2, c2 = sq_to_rc(sq)
                assert r2 == row and c2 == col
        # boundary: corners
        assert rc_to_sq(0, 0) == 0
        assert rc_to_sq(9, 8) == 89
        r, c = sq_to_rc(89)
        assert r == 9 and c == 8

    def test_capture_bit_isolated(self):
        """DATA-03: is_capture bit does not bleed into from/to."""
        # Move from 10 to 20, not capture
        m_nocap = encode_move(10, 20, False)
        # Same squares, with capture
        m_cap = encode_move(10, 20, True)
        assert (m_cap & 0x10000) == 0x10000  # bit 16 set
        assert (m_nocap & 0x10000) == 0       # bit 16 clear
        assert (m_cap & 0xFFFF) == (m_nocap & 0xFFFF)  # lower 16 bits same
