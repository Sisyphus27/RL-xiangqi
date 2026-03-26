"""Tests for Task 1: signal, interaction flag, and coordinate conversion."""

import pytest
from PyQt6.QtCore import QPointF
from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.ui.board import QXiangqiBoard


@pytest.fixture
def board_with_engine(qtbot):
    """QXiangqiBoard with XiangqiEngine for interaction tests."""
    state = XiangqiState.starting()
    engine = XiangqiEngine.starting()
    b = QXiangqiBoard(state=state, engine=engine)
    qtbot.addWidget(b)
    return b


class TestMoveAppliedSignal:
    """Test 1: QXiangqiBoard has move_applied signal with (int, int, int) signature."""

    def test_move_applied_signal_exists(self, board_with_engine):
        """QXiangqiBoard has a move_applied pyqtSignal."""
        board = board_with_engine
        assert hasattr(board, 'move_applied'), "QXiangqiBoard must have move_applied signal"
        # Check it's a pyqtSignal by verifying it has a connect method
        assert hasattr(board.move_applied, 'connect'), "move_applied must be a signal with connect method"


class TestInteractiveFlag:
    """Test 2: QXiangqiBoard has _interactive flag defaulting to True."""

    def test_interactive_flag_exists_and_true(self, board_with_engine):
        """QXiangqiBoard._interactive defaults to True."""
        board = board_with_engine
        assert hasattr(board, '_interactive'), "QXiangqiBoard must have _interactive attribute"
        assert board._interactive is True, "_interactive must default to True"

    def test_set_interactive_method_exists(self, board_with_engine):
        """QXiangqiBoard has set_interactive method."""
        board = board_with_engine
        assert hasattr(board, 'set_interactive'), "QXiangqiBoard must have set_interactive method"
        assert callable(board.set_interactive), "set_interactive must be callable"

    def test_set_interactive_changes_flag(self, board_with_engine):
        """set_interactive(True/False) changes _interactive flag."""
        board = board_with_engine
        board.set_interactive(False)
        assert board._interactive is False
        board.set_interactive(True)
        assert board._interactive is True


class TestSceneToBoard:
    """Test 3: _scene_to_board converts scene coords to board (row, col) accounting for 0.6*cell offset."""

    def test_scene_to_board_method_exists(self, board_with_engine):
        """QXiangqiBoard has _scene_to_board method."""
        board = board_with_engine
        assert hasattr(board, '_scene_to_board'), "QXiangqiBoard must have _scene_to_board method"
        assert callable(board._scene_to_board), "_scene_to_board must be callable"

    def test_scene_to_board_converts_top_left(self, board_with_engine):
        """(0.6*cell, 0.6*cell) in scene maps to (row=0, col=0)."""
        board = board_with_engine
        cell = board._cell
        result = board._scene_to_board(QPointF(0.6 * cell, 0.6 * cell))
        assert result is not None
        row, col = result
        assert row == 0
        assert col == 0

    def test_scene_to_board_converts_center(self, board_with_engine):
        """(5.6*cell, 5.6*cell) in scene maps to (row=5, col=5)."""
        board = board_with_engine
        cell = board._cell
        result = board._scene_to_board(QPointF(5.6 * cell, 5.6 * cell))
        assert result is not None
        row, col = result
        assert row == 5
        assert col == 5

    def test_scene_to_board_converts_bottom_right(self, board_with_engine):
        """(9.5*cell, 9.5*cell) in scene maps to (row=9, col=8)."""
        board = board_with_engine
        cell = board._cell
        # 9.5 - 0.6 = 8.9 -> round = 9 (valid row)
        # 9.5 - 0.6 = 8.9 -> round = 9 -> out of bounds for col (max 8)
        # Use 9.4 for col to get 8.8 -> round = 9? Actually:
        # (9.5*cell, 9.5*cell): col=round(9.5-0.6)=round(8.9)=9 (FAIL, col 9 out of range)
        # (9.4*cell, 9.5*cell): col=round(9.4-0.6)=round(8.8)=9 -> FAIL
        # (9.3*cell, 9.5*cell): col=round(9.3-0.6)=round(8.7)=9 -> FAIL
        # (9.1*cell, 9.5*cell): col=round(9.1-0.6)=round(8.5)=8 (OK), row=round(9.5-0.6)=9 (OK)
        result = board._scene_to_board(QPointF(9.1 * cell, 9.5 * cell))
        assert result is not None
        row, col = result
        assert row == 9
        assert col == 8

    def test_scene_to_board_returns_none_outside_board(self, board_with_engine):
        """Scene coords outside grid return None."""
        board = board_with_engine
        cell = board._cell
        # Just outside right: x=10.1*cell → col=round(9.5)=10 (out of bounds)
        result = board._scene_to_board(QPointF(10.1 * cell, 5.0 * cell))
        assert result is None
        # Just below bottom: y=10.1*cell → row=round(9.5)=10 (out of bounds)
        result = board._scene_to_board(QPointF(5.0 * cell, 10.1 * cell))
        assert result is None


class TestMousePressEvent:
    """Test 4: mousePressEvent checks _interactive flag and ignores clicks when False."""

    def test_mouse_press_event_exists(self, board_with_engine):
        """QXiangqiBoard has mousePressEvent method."""
        board = board_with_engine
        assert hasattr(board, 'mousePressEvent'), "QXiangqiBoard must have mousePressEvent method"
        assert callable(board.mousePressEvent), "mousePressEvent must be callable"

    def test_mouse_press_disabled_does_nothing(self, board_with_engine, qtbot):
        """When _interactive=False, clicking has no effect (no error raised)."""
        board = board_with_engine
        board.set_interactive(False)
        cell = board._cell
        # Try to click a piece location — should be silently ignored
        try:
            from PyQt6.QtGui import QMouseEvent
            from PyQt6.QtCore import Qt
            # Simulate click on red pawn at row 6, col 0
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPointF(0.6 * cell, 6.6 * cell),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            board.mousePressEvent(event)
        except Exception as exc:
            pytest.fail(f"mousePressEvent raised an exception when disabled: {exc}")
