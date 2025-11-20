from abc import ABC, abstractmethod
from collections.abc import Sequence

from playwright.sync_api import Page

from src.providers.types import Episode


class BaseProvider(ABC):
    """Abstract base class for a series provider."""

    def __init__(self, page: Page):
        self.page = page

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
    def get_series_episodes(self, url: str) -> Sequence[Episode]:
        """
        Get the list of all episodes for a series.

        Args:
            url: The URL of the series page to fetch episodes from.

        Returns:
            A list of dictionaries, where each dictionary represents an
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
