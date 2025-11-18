from abc import ABC, abstractmethod
from typing import Any

import requests

from src.constants import Series


class BaseProvider(ABC):
    """Abstract base class for a series provider."""

    def __init__(self, session: requests.Session):
        self.session = session

    @classmethod
    @abstractmethod
    def can_handle_url(cls, url: str) -> bool:
        """
        Check if the provider can handle the given URL.

        Args:
            url: The URL to check.

        Returns:
            True if the provider can handle the URL, False otherwise.
        """
        pass

    @abstractmethod
    def get_series_episodes(self, series_info: Series) -> tuple[int, list[dict[str, Any]]]:
        """
        Get the list of episodes for a series.

        Args:
            series_info: A dictionary containing information about the series,
                         including the URL.

        Returns:
            A tuple containing:
            - The total number of episodes found.
            - A list of dictionaries, where each dictionary represents a new
              episode and contains details like season, episode number, and
              download link.
        """
        pass

    @abstractmethod
    def get_download_url(self, episode_link: str) -> str:
        """
        Get the final download URL for an episode.

        Args:
            episode_link: The initial link for the episode.

        Returns:
            The final, direct download URL.
        """
        pass
