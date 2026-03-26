"""Tests for AIWorker QThread worker object."""
import pytest
from unittest.mock import Mock

from PyQt6.QtCore import QEventLoop, QTimer

from src.xiangqi.ai.base import AIPlayer, EngineSnapshot
from src.xiangqi.engine.engine import XiangqiEngine


class TestAIWorkerInit:
    """Test 1: AIWorker accepts AI player and snapshot in constructor."""

    def test_worker_accepts_ai_player_and_snapshot(self, qapp):
        """AIWorker constructor accepts AIPlayer and EngineSnapshot."""
        from src.xiangqi.controller.ai_worker import AIWorker

        engine = XiangqiEngine.starting()
        snapshot = EngineSnapshot.from_engine(engine)
        ai_player = Mock(spec=AIPlayer)

        worker = AIWorker(ai_player, snapshot)

        assert worker is not None


class TestAIWorkerCompute:
    """Test 2: AIWorker.compute() emits move_ready with valid move."""

    def test_compute_emits_move_ready(self, qapp):
        """AIWorker.compute() calls suggest_move and emits move_ready."""
        from src.xiangqi.controller.ai_worker import AIWorker

        engine = XiangqiEngine.starting()
        snapshot = EngineSnapshot.from_engine(engine)

        # Create mock AI that returns a specific move
        ai_player = Mock(spec=AIPlayer)
        legal_moves = snapshot.legal_moves
        test_move = legal_moves[0] if legal_moves else 0
        ai_player.suggest_move.return_value = test_move

        worker = AIWorker(ai_player, snapshot)

        # Track signal emission
        emitted_moves = []
        worker.move_ready.connect(lambda m: emitted_moves.append(m))

        # Call compute directly (synchronous for testing)
        worker.compute()

        # Verify suggest_move was called with snapshot
        ai_player.suggest_move.assert_called_once_with(snapshot)

        # Verify signal was emitted with the move
        assert len(emitted_moves) == 1
        assert emitted_moves[0] == test_move

    def test_compute_does_not_emit_when_no_legal_moves(self, qapp):
        """AIWorker.compute() does not emit if no legal moves available."""
        from src.xiangqi.controller.ai_worker import AIWorker

        # Create snapshot with empty legal_moves
        snapshot = Mock(spec=EngineSnapshot)
        snapshot.legal_moves = []

        ai_player = Mock(spec=AIPlayer)
        ai_player.suggest_move.return_value = None

        worker = AIWorker(ai_player, snapshot)

        emitted_moves = []
        worker.move_ready.connect(lambda m: emitted_moves.append(m))

        worker.compute()

        assert len(emitted_moves) == 0


class TestAIWorkerError:
    """Test 3: AIWorker.compute() handles exception and emits error."""

    def test_compute_emits_error_on_exception(self, qapp):
        """AIWorker.compute() emits error signal when AI raises exception."""
        from src.xiangqi.controller.ai_worker import AIWorker

        engine = XiangqiEngine.starting()
        snapshot = EngineSnapshot.from_engine(engine)

        ai_player = Mock(spec=AIPlayer)
        ai_player.suggest_move.side_effect = RuntimeError("AI crashed")

        worker = AIWorker(ai_player, snapshot)

        emitted_errors = []
        worker.error.connect(lambda e: emitted_errors.append(e))

        worker.compute()

        assert len(emitted_errors) == 1
        assert "AI crashed" in emitted_errors[0]
