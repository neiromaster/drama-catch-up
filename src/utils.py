"""Utility functions for the application."""

import logging


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

    try:
        if carriage_return:
            print(output_message, end="")
        else:
            print(output_message)
    except UnicodeEncodeError:
        # Fallback to ASCII representation if Unicode fails
        if carriage_return:
            print(output_message.encode("ascii", errors="replace").decode("ascii"), end="")
        else:
            print(output_message.encode("ascii", errors="replace").decode("ascii"))

    if bottom > 0:
        print("\n" * (bottom - 1))


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)
