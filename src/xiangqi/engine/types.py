from enum import IntEnum
from typing import Tuple

# ─── constants ───────────────────────────────────────────────────────────────
ROWS, COLS = 10, 9
NUM_SQUARES = ROWS * COLS  # 90

# ─── Piece IntEnum (DATA-01, DATA-02) ────────────────────────────────────────
_PIECE_CHARS = {
    0: '　',    # full-width space for empty
    +1: '帅', +2: '仕', +3: '相', +4: '马', +5: '车', +6: '炮', +7: '兵',
    -1: '将', -2: '士', -3: '象', -4: '馬', -5: '車', -6: '砲', -7: '卒',
}


class Piece(IntEnum):
    EMPTY = 0
    R_SHUAI = +1   # red general (帅)
    B_JIANG = -1   # black general (将)
    R_SHI = +2     # red advisor (仕)
    B_SHI = -2     # black advisor (士)
    R_XIANG = +3   # red elephant (相)
    B_XIANG = -3   # black elephant (象)
    R_MA = +4      # red horse (马)
    B_MA = -4      # black horse (馬)
    R_CHE = +5     # red chariot (车)
    B_CHE = -5     # black chariot (車)
    R_PAO = +6     # red cannon (炮)
    B_PAO = -6     # black cannon (砲)
    R_BING = +7    # red soldier (兵)
    B_ZU = -7      # black soldier (卒)

    def __repr__(self) -> str:
        return _PIECE_CHARS[self.value]

    def __str__(self) -> str:
        return _PIECE_CHARS[self.value]


# ─── move encoding/decoding (DATA-03) ────────────────────────────────────────
# Bit layout (16-bit integer):
#   bits 0-8:  from_sq  (9 bits, range 0-89)
#   bits 9-15: to_sq    (7 bits, range 0-89)
#   bit  16:  is_capture (single flag bit)
_FROM_MASK = 0x1FF     # bits 0-8  (mask for from_sq)
_TO_MASK   = 0xFE00   # bits 9-15 (mask for to_sq << 9)
_CAP_MASK  = 0x10000   # bit 16


def rc_to_sq(row: int, col: int) -> int:
    """Flat square index: row * 9 + col. Range 0-89."""
    return row * COLS + col


def sq_to_rc(sq: int) -> Tuple[int, int]:
    """Reverse flat index: (row, col) = divmod(sq, 9)."""
    return divmod(sq, COLS)


def encode_move(from_sq: int, to_sq: int, is_capture: bool = False) -> int:
    """16-bit encoding: bits 0-8=from_sq, bits 9-17=to_sq, bit 16=is_capture."""
    return (from_sq & _FROM_MASK) | ((to_sq << 9) & _TO_MASK) | (int(is_capture) << 16)


def decode_move(move: int) -> Tuple[int, int, bool]:
    """Reverse the 16-bit encoding."""
    from_sq =  move        & _FROM_MASK
    to_sq   = (move >> 9)  & 0x7F    # bits 9-15 = 7 bits for to_sq 0-89
    capture =  (move >> 16) & 0x1
    return from_sq, to_sq, bool(capture)
