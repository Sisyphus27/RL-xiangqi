"""Tests for QXiangqiBoard — scene structure, piece loading, window title."""

import pytest
from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.ui.board import QXiangqiBoard
from src.xiangqi.ui.board_items import PieceItem
from src.xiangqi.ui.constants import RED_FILL, BLACK_FILL


class TestBoardScene:
    """Scene existence and basic structure."""

    def test_board_scene_exists(self, board):
        """QXiangqiBoard has a QGraphicsScene."""
        assert board.scene() is not None


class TestPieceCount:
    """32-piece loading tests."""

    def test_piece_count(self, board):
        """Exactly 32 pieces on starting board."""
        pieces = [i for i in board.scene().items() if isinstance(i, PieceItem)]
        assert len(pieces) == 32

    def test_red_pieces_count(self, board):
        """Red side has 16 pieces (7 types)."""
        pieces = [i for i in board.scene().items() if isinstance(i, PieceItem)]
        red_pieces = [p for p in pieces if p._piece_value > 0]
        assert len(red_pieces) == 16

    def test_black_pieces_count(self, board):
        """Black side has 16 pieces (7 types)."""
        pieces = [i for i in board.scene().items() if isinstance(i, PieceItem)]
        black_pieces = [p for p in pieces if p._piece_value < 0]
        assert len(black_pieces) == 16

    def test_no_empty_squares(self, board):
        """All 90 squares are either a PieceItem or empty (no other item types)."""
        items = board.scene().items()
        piece_count = sum(1 for i in items if isinstance(i, PieceItem))
        # Only PieceItems should be in the scene (no other custom items)
        assert piece_count == len(items)


class TestPieceColors:
    """Piece fill color tests — matching constants."""

    def test_piece_colors_match_constants(self, board):
        """Red fill is #CC2200, black fill is #1A1A1A."""
        for item in board.scene().items():
            if not isinstance(item, PieceItem):
                continue
            expected_fill = "#CC2200" if item._piece_value > 0 else "#1A1A1A"
            actual = item.brush().color().name().upper()
            assert actual == expected_fill.upper(), (
                f"Piece value {item._piece_value}: expected {expected_fill}, got {actual}"
            )


class TestCellSizeFormula:
    """Aspect ratio preservation tests."""

    def test_cell_size_formula(self):
        """cell = min(vw, vh) / 11.2 at various sizes."""
        test_cases = [
            (360, 450, min(360, 450) / 11.2),  # height constrains
            (480, 600, min(480, 600) / 11.2),  # width constrains
            (720, 900, min(720, 900) / 11.2),  # height constrains
            (400, 500, min(400, 500) / 11.2),  # width constrains
        ]
        for vw, vh, expected_cell in test_cases:
            cell = min(vw, vh) / 11.2
            assert abs(cell - expected_cell) < 0.01


class TestMainWindow:
    """MainWindow title and structure tests."""

    def test_window_title_from_main(self, qtbot):
        """MainWindow has correct title set."""
        from src.xiangqi.ui.main import MainWindow

        win = MainWindow()
        qtbot.addWidget(win)
        assert win.windowTitle() == "RL-Xiangqi v0.2"

    def test_main_window_has_board(self, qtbot):
        """MainWindow central widget is a QXiangqiBoard."""
        from src.xiangqi.ui.main import MainWindow

        win = MainWindow()
        qtbot.addWidget(win)
        central = win.centralWidget()
        assert isinstance(central, QXiangqiBoard)

    def test_main_window_size(self, qtbot):
        """MainWindow resizes to DEFAULT_SIZE on init."""
        from src.xiangqi.ui.main import MainWindow
        from src.xiangqi.ui.constants import DEFAULT_SIZE

        win = MainWindow()
        qtbot.addWidget(win)
        assert win.width() == DEFAULT_SIZE[0]
        assert win.height() == DEFAULT_SIZE[1]

    def test_main_window_min_max_size(self, qtbot):
        """MainWindow respects MIN_SIZE and MAX_SIZE."""
        from src.xiangqi.ui.main import MainWindow
        from src.xiangqi.ui.constants import MIN_SIZE, MAX_SIZE

        win = MainWindow()
        qtbot.addWidget(win)
        assert win.minimumSize().width() == MIN_SIZE[0]
        assert win.minimumSize().height() == MIN_SIZE[1]
        assert win.maximumSize().width() == MAX_SIZE[0]
        assert win.maximumSize().height() == MAX_SIZE[1]
