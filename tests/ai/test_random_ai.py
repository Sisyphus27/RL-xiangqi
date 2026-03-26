"""Tests for RandomAI implementation."""
import pytest

from src.xiangqi.ai import AIPlayer, EngineSnapshot, RandomAI
from src.xiangqi.engine.engine import XiangqiEngine


@pytest.fixture
def engine():
    return XiangqiEngine.starting()


@pytest.fixture
def snapshot(engine):
    return EngineSnapshot.from_engine(engine)


def test_random_ai_is_ai_player():
    """RandomAI is a valid AIPlayer implementation."""
    ai = RandomAI()
    assert isinstance(ai, AIPlayer)


def test_random_ai_returns_legal_move(snapshot):
    """RandomAI returns a move from snapshot.legal_moves."""
    ai = RandomAI(seed=42)
    move = ai.suggest_move(snapshot)
    assert move is not None
    assert move in snapshot.legal_moves


def test_random_ai_returns_none_when_no_moves():
    """RandomAI returns None when legal_moves is empty."""
    ai = RandomAI()
    # Create snapshot with empty legal_moves
    engine = XiangqiEngine.starting()
    snapshot = EngineSnapshot(
        board=engine.board.copy(),
        turn=engine.turn,
        legal_moves=[],
    )
    assert ai.suggest_move(snapshot) is None


def test_random_ai_seed_reproducibility(snapshot):
    """Same seed produces same move sequence."""
    ai1 = RandomAI(seed=12345)
    ai2 = RandomAI(seed=12345)

    moves1 = [ai1.suggest_move(snapshot) for _ in range(5)]
    moves2 = [ai2.suggest_move(snapshot) for _ in range(5)]

    assert moves1 == moves2


def test_random_ai_different_seeds_differ(snapshot):
    """Different seeds likely produce different first moves."""
    ai1 = RandomAI(seed=1)
    ai2 = RandomAI(seed=2)

    # Run multiple times to reduce false positive
    moves1 = [ai1.suggest_move(snapshot) for _ in range(10)]
    moves2 = [ai2.suggest_move(snapshot) for _ in range(10)]

    # Very unlikely to be identical with different seeds
    assert moves1 != moves2
