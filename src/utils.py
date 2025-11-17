"""Utility functions for the application."""

import logging
import time
from typing import Any

import requests


def log(message: str, indent: int = 0, top: int = 0, bottom: int = 0, carriage_return: bool = False) -> None:
    """
    Custom print function that supports indentation, padding, and optional carriage return.

    Args:
        message: The message to print.
        indent: Number of indentation units (2 spaces each).
        top: Number of empty lines to print before the message.
        bottom: Number of empty lines to print after the message.
        carriage_return: If True, prepends '\r' to the message for in-place updates.
    """
    if top > 0:
        print("\n" * (top - 1))

    prefix = "  " * indent

    output_message = f"{prefix}{message}"
    if carriage_return:
        output_message = f"\r{output_message}"
        print_kwargs = {"end": ""}
    else:
        print_kwargs = {}

    try:
        print(output_message, **print_kwargs)
    except UnicodeEncodeError:
        print(output_message.encode("ascii", errors="replace").decode("ascii"), **print_kwargs)

    if bottom > 0:
        print("\n" * (bottom - 1))


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
