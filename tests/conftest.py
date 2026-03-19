"""Shared pytest fixtures for Phase 1 tests."""
import numpy as np
import pytest

from src.xiangqi.engine.state import XiangqiState
from src.xiangqi.engine.types import Piece, ROWS, COLS

@pytest.fixture
def empty_board() -> np.ndarray:
    """An empty 10x9 board (all zeros)."""
    return np.zeros((ROWS, COLS), dtype=np.int8)

@pytest.fixture
def starting_board() -> np.ndarray:
    """The standard starting position board array."""
    board, _ = XiangqiState.starting().board, None
    return board

@pytest.fixture
def starting_state() -> XiangqiState:
    """The standard starting XiangqiState (red to move)."""
    return XiangqiState.starting()
