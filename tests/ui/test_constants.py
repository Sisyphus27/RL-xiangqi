"""Tests for UI constants — color values, sizes, ratios."""

import pytest


def test_color_constants():
    """All color constants have correct hex values from UI-SPEC."""
    from src.xiangqi.ui.constants import (
        BOARD_BG,
        GRID_COLOR,
        RED_FILL,
        BLACK_FILL,
        PIECE_TEXT_COLOR,
        PIECE_STROKE_COLOR,
    )
    assert BOARD_BG == "#7BA05B"
    assert GRID_COLOR == "#2D5A1B"
    assert RED_FILL == "#CC2200"
    assert BLACK_FILL == "#1A1A1A"
    assert PIECE_TEXT_COLOR == "#FFFFFF"
    assert PIECE_STROKE_COLOR == "#FFFFFF"


def test_text_color_constants():
    """River and coordinate text colors match grid color."""
    from src.xiangqi.ui.constants import RIVER_TEXT_COLOR, COORD_TEXT_COLOR, GRID_COLOR

    assert RIVER_TEXT_COLOR == GRID_COLOR
    assert COORD_TEXT_COLOR == GRID_COLOR


def test_size_constants():
    """Window size constants match UI-SPEC."""
    from src.xiangqi.ui.constants import DEFAULT_SIZE, MIN_SIZE, MAX_SIZE

    assert DEFAULT_SIZE == (480, 600)
    assert MIN_SIZE == (360, 450)
    assert MAX_SIZE == (720, 900)


def test_size_constraints():
    """MIN_SIZE <= DEFAULT_SIZE <= MAX_SIZE."""
    from src.xiangqi.ui.constants import DEFAULT_SIZE, MIN_SIZE, MAX_SIZE

    assert MIN_SIZE[0] <= DEFAULT_SIZE[0] <= MAX_SIZE[0]
    assert MIN_SIZE[1] <= DEFAULT_SIZE[1] <= MAX_SIZE[1]


def test_ratio_constants():
    """Font/size ratio constants have expected values."""
    from src.xiangqi.ui.constants import (
        CELL_RATIO,
        PIECE_FONT_RATIO,
        RIVER_FONT_RATIO,
        COORD_FONT_RATIO,
    )

    assert CELL_RATIO == 0.80
    assert PIECE_FONT_RATIO == 0.56
    assert RIVER_FONT_RATIO == 0.28
    assert COORD_FONT_RATIO == 0.22


def test_ratio_range():
    """Ratios are between 0 and 1."""
    from src.xiangqi.ui.constants import (
        CELL_RATIO,
        PIECE_FONT_RATIO,
        RIVER_FONT_RATIO,
        COORD_FONT_RATIO,
    )

    for ratio, name in [
        (CELL_RATIO, "CELL_RATIO"),
        (PIECE_FONT_RATIO, "PIECE_FONT_RATIO"),
        (RIVER_FONT_RATIO, "RIVER_FONT_RATIO"),
        (COORD_FONT_RATIO, "COORD_FONT_RATIO"),
    ]:
        assert 0.0 < ratio <= 1.0, f"{name} should be in (0, 1], got {ratio}"
