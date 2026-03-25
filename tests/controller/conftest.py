"""Pytest fixtures for controller tests."""
import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Ensure QApplication exists for Qt signal tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
