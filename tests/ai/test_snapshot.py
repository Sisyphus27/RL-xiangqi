"""Tests for EngineSnapshot dataclass - thread-safe state capture."""
import dataclasses

import numpy as np
import pytest

from src.xiangqi.engine.engine import XiangqiEngine


class TestEngineSnapshotFromEngine:
    """Test EngineSnapshot.from_engine() creation."""

    def test_snapshot_from_engine(self):
        """EngineSnapshot.from_engine(engine) creates snapshot with board, turn, legal_moves."""
        from src.xiangqi.ai.base import EngineSnapshot

        engine = XiangqiEngine.starting()
        snapshot = EngineSnapshot.from_engine(engine)

        # Verify board matches
        assert snapshot.board.shape == (10, 9)
        assert np.array_equal(snapshot.board, engine.board)

        # Verify turn matches
        assert snapshot.turn == engine.turn  # +1 for red

        # Verify legal_moves matches
        assert snapshot.legal_moves == list(engine.legal_moves())

    def test_snapshot_board_is_copy(self):
        """Snapshot board is a deep copy (np.shares_memory returns False)."""
        from src.xiangqi.ai.base import EngineSnapshot

        engine = XiangqiEngine.starting()
        snapshot = EngineSnapshot.from_engine(engine)

        # Board must be a copy, not sharing memory with engine's board
        assert not np.shares_memory(snapshot.board, engine.board)

    def test_snapshot_is_frozen(self):
        """Snapshot is frozen (cannot assign to fields)."""
        from src.xiangqi.ai.base import EngineSnapshot

        engine = XiangqiEngine.starting()
        snapshot = EngineSnapshot.from_engine(engine)

        # Attempting to assign to a frozen dataclass should raise FrozenInstanceError
        with pytest.raises(dataclasses.FrozenInstanceError):
            snapshot.board = np.zeros((10, 9), dtype=np.int8)

    def test_snapshot_legal_moves_is_copy(self):
        """legal_moves is a list copy (not reference to engine's internal)."""
        from src.xiangqi.ai.base import EngineSnapshot

        engine = XiangqiEngine.starting()
        snapshot = EngineSnapshot.from_engine(engine)

        # Get original legal moves from engine
        original_moves = list(engine.legal_moves())

        # Modify snapshot's legal_moves
        snapshot.legal_moves.append(999999)  # Add an invalid move

        # Engine's legal_moves should be unchanged
        assert list(engine.legal_moves()) == original_moves
        assert 999999 not in list(engine.legal_moves())
