"""Tests for AIPlayer abstract base class - contract verification."""
import pytest

from src.xiangqi.ai.base import AIPlayer, EngineSnapshot


class TestAIPlayerContract:
    """Test that AIPlayer ABC enforces the correct contract."""

    def test_aiplayer_is_abstract(self):
        """AIPlayer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AIPlayer()

    def test_aiplayer_requires_suggest_move(self):
        """Subclass without suggest_move raises TypeError."""
        class IncompleteAI(AIPlayer):
            pass

        with pytest.raises(TypeError):
            IncompleteAI()

    def test_aiplayer_subclass_works(self):
        """Subclass with suggest_move can be instantiated."""
        class MinimalAI(AIPlayer):
            def suggest_move(self, snapshot: EngineSnapshot):
                return None

        ai = MinimalAI()
        assert ai is not None

    def test_aiplayer_subclass_can_return_move(self):
        """Subclass can return a move from suggest_move."""
        class TestAI(AIPlayer):
            def suggest_move(self, snapshot: EngineSnapshot):
                # Return first legal move if available
                if snapshot.legal_moves:
                    return snapshot.legal_moves[0]
                return None

        from src.xiangqi.engine.engine import XiangqiEngine

        engine = XiangqiEngine.starting()
        snapshot = EngineSnapshot.from_engine(engine)
        ai = TestAI()

        move = ai.suggest_move(snapshot)
        assert move is not None
        assert move in snapshot.legal_moves
