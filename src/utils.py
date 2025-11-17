"""Utility functions for the application."""

import logging
import time
from typing import Any

import requests


def log(message: str, pad: int = 0, top: int = 0, bottom: int = 0, left_pad_char: str = " ") -> None:
    """
    Print a message with custom padding and indentation.

    Args:
        message: The message to print
        pad: Number of padding units to add to the left (each unit is 2 spaces)
        top: Number of empty lines to add before the message
        bottom: Number of empty lines to add after the message
        left_pad_char: Character to use for left padding (default is space)
    """
    # Add top padding
    for _ in range(top):
        print()

    # Calculate left padding
    left_padding = left_pad_char * (pad * 2)

    # Print the message with left padding
    print(f"{left_padding}{message}")

    # Add bottom padding
    for _ in range(bottom):
        print()


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def get_with_retries(
    session: requests.Session,
    url: str,
    retries: int = 3,
    backoff_factor: int = 5,
    timeout: int = 30,
    **kwargs: Any,
) -> requests.Response:
    """Wrapper for session.get with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                sleep_time = backoff_factor * (2**attempt)
                print(f"    ⏳ Ошибка '{e}', повторная попытка через {sleep_time} секунд...")
                time.sleep(sleep_time)
            else:
                raise e
    # This line should never be reached due to the raise in the loop, but added for type checking
    raise RuntimeError("Unexpected flow in get_with_retries")
