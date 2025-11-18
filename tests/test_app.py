from typing import Any
from unittest.mock import patch

from src.app import run_check


def test_run_check_no_config():
    """
    Tests that run_check returns the default interval when no config is found.
    """
    with patch("src.app.load_config", return_value=None):
        interval = run_check()
        assert interval == 10


def test_run_check_no_series():
    """
    Tests that run_check returns the configured interval when no series are found.
    """
    config: dict[str, Any] = {"settings": {"check_interval_minutes": 15}, "series": []}
    with patch("src.app.load_config", return_value=config):
        interval = run_check()
        assert interval == 15
