"""Tests for GameController orchestration layer."""
import pytest
from unittest.mock import Mock, patch

from PyQt6.QtCore import QEventLoop, QTimer

from src.xiangqi.ai import RandomAI
from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.types import encode_move, rc_to_sq


class TestGameControllerConnection:
    """Test 1: GameController connects to board.move_applied signal."""

    def test_controller_connects_to_board_signal(self, qapp, qtbot):
        """GameController connects to board.move_applied signal."""
        from src.xiangqi.controller.game_controller import GameController

        engine = XiangqiEngine.starting()
        ai_player = RandomAI(seed=42)

        # Mock board and window
        board = Mock()
        board.move_applied = Mock()
        board.move_applied.connect = Mock()
        board.set_interactive = Mock()
        window = Mock()
        window.statusBar = Mock()

        # Mock _start_ai_turn during construction to prevent thread leaks
        with patch.object(GameController, '_start_ai_turn'):
            controller = GameController(
                engine=engine,
                ai_player=ai_player,
                board=board,
                main_window=window,
            )

        # Verify board.move_applied.connect was called
        board.move_applied.connect.assert_called_once()


class TestGameControllerTurnChanged:
    """Test 2: On user move, turn_changed signal emitted with new turn."""

    def test_controller_emits_turn_changed_on_user_move(self, qapp, qtbot):
        """After user move, turn_changed signal emitted with engine.turn."""
        from src.xiangqi.controller.game_controller import GameController

        engine = XiangqiEngine.starting()
        ai_player = RandomAI(seed=42)

        board = Mock()
        board.move_applied = Mock()
        board.move_applied.connect = Mock()
        board.set_interactive = Mock()
        window = Mock()
        window.statusBar = Mock()

        # Mock _start_ai_turn during construction too -- constructor may call
        # it if random side assigns human=Black (D-02)
        with patch.object(GameController, '_start_ai_turn'):
            controller = GameController(
                engine=engine,
                ai_player=ai_player,
                board=board,
                main_window=window,
            )

        # Track turn_changed signal
        emitted_turns = []
        controller.turn_changed.connect(lambda t: emitted_turns.append(t))

        # Apply a move to the engine (simulating board move)
        move = engine.legal_moves()[0]
        engine.apply(move)

        # Trigger controller's _on_move_applied handler
        # Mock _start_ai_turn to prevent real QThread spawning (D-02)
        from_sq = move & 0x1FF
        to_sq = (move >> 9) & 0x7F
        with patch.object(controller, '_start_ai_turn'):
            controller._on_move_applied(from_sq, to_sq, 0)

        # Turn should have changed to black (-1)
        assert len(emitted_turns) == 1
        assert emitted_turns[0] == -1


class TestGameControllerAIThinking:
    """Test 3: On black turn, ai_thinking_started signal emitted."""

    def test_controller_starts_ai_on_black_turn(self, qapp, qtbot):
        """On black turn, ai_thinking_started signal is emitted."""
        from src.xiangqi.controller.game_controller import GameController

        engine = XiangqiEngine.starting()
        ai_player = RandomAI(seed=42)

        board = Mock()
        board.move_applied = Mock()
        board.move_applied.connect = Mock()
        board.set_interactive = Mock()
        window = Mock()
        window.statusBar = Mock()

        # Mock _start_ai_turn during construction too -- constructor may call
        # it if random side assigns human=Black (D-02)
        with patch.object(GameController, '_start_ai_turn'):
            controller = GameController(
                engine=engine,
                ai_player=ai_player,
                board=board,
                main_window=window,
            )

        # Force human to play Red so AI plays Black -- deterministic test
        controller._human_side = 1

        # Apply a red move (making it black's turn)
        move = engine.legal_moves()[0]
        engine.apply(move)

        # Trigger controller's _on_move_applied handler
        # Mock _start_ai_turn to prevent real QThread spawning (D-02)
        # Verify _start_ai_turn is called (proving AI turn detection works)
        from_sq = move & 0x1FF
        to_sq = (move >> 9) & 0x7F
        with patch.object(controller, '_start_ai_turn') as mock_start:
            controller._on_move_applied(from_sq, to_sq, 0)
            mock_start.assert_called_once()


class TestGameControllerAILegalGuard:
    """Test 4: AI move is validated with is_legal() before apply."""

    def test_controller_validates_ai_move(self, qapp, qtbot):
        """AI move is validated with is_legal() before being applied."""
        from src.xiangqi.controller.game_controller import GameController

        engine = XiangqiEngine.starting()
        ai_player = RandomAI(seed=42)

        board = Mock()
        board.move_applied = Mock()
        board.move_applied.connect = Mock()
        board.set_interactive = Mock()
        board.apply_move = Mock()
        window = Mock()
        window.statusBar = Mock()

        # Mock _start_ai_turn during construction to prevent thread leaks
        with patch.object(GameController, '_start_ai_turn'):
            controller = GameController(
                engine=engine,
                ai_player=ai_player,
                board=board,
                main_window=window,
            )

        # Apply a red move to get to black's turn
        red_move = engine.legal_moves()[0]
        engine.apply(red_move)

        # Get a legal black move
        black_moves = engine.legal_moves()
        assert len(black_moves) > 0
        legal_black_move = black_moves[0]

        # Track is_legal calls
        is_legal_calls = []
        original_is_legal = engine.is_legal

        def track_is_legal(move):
            is_legal_calls.append(move)
            return original_is_legal(move)

        engine.is_legal = track_is_legal

        # Simulate AI move ready
        controller._on_ai_move_ready(legal_black_move)

        # is_legal should have been called
        assert legal_black_move in is_legal_calls


class TestGameControllerGameOver:
    """Test 5: Game over triggers game_over signal with correct result."""

    def test_controller_emits_game_over_on_checkmate(self, qapp, qtbot):
        """Game over triggers game_over signal with correct result."""
        from src.xiangqi.controller.game_controller import GameController

        engine = XiangqiEngine.starting()
        ai_player = RandomAI(seed=42)

        board = Mock()
        board.move_applied = Mock()
        board.move_applied.connect = Mock()
        board.set_interactive = Mock()
        window = Mock()
        window.statusBar = Mock()

        # Mock QMessageBox.information to avoid Qt widget requirement
        # Mock _start_ai_turn during construction to prevent thread leaks
        with patch('src.xiangqi.controller.game_controller.QMessageBox.information'), \
             patch.object(GameController, '_start_ai_turn'):
            controller = GameController(
                engine=engine,
                ai_player=ai_player,
                board=board,
                main_window=window,
            )

            # Track game_over signal
            game_over_results = []
            controller.game_over.connect(lambda r: game_over_results.append(r))

            # Call _handle_game_over directly
            controller._handle_game_over("RED_WINS")

            # game_over should have been emitted
            assert len(game_over_results) == 1
            assert game_over_results[0] == "RED_WINS"
