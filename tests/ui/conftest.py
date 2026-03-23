"""
Pytest fixtures for UI tests.

Provides:
  - starting_state: XiangqiState in standard starting position
  - board: QXiangqiBoard widget with qtbot lifecycle management
"""

import pytest
from src.xiangqi.engine.state import XiangqiState


@pytest.fixture
def starting_state() -> XiangqiState:
    """Standard starting XiangqiState (red to move, 32 pieces)."""
    return XiangqiState.starting()


@pytest.fixture
def board(qtbot):
    """QXiangqiBoard widget with starting position; managed by qtbot."""
    from src.xiangqi.ui.board import QXiangqiBoard

    b = QXiangqiBoard()
    qtbot.addWidget(b)
    return b
