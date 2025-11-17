from abc import ABC, abstractmethod
from typing import Any


class BaseDownloader(ABC):
    """Abstract base class for a downloader."""

    @abstractmethod
    def download(
        self,
        url: str,
        series_name: str,
        season: int,
        episode: int,
        output_dir: str,
        **kwargs: Any,
    ) -> bool:
        """
        Download a single episode.

        Args:
            url: The download URL for the episode.
            series_name: The name of the series.
            season: The season number.
            episode: The episode number.
            output_dir: The directory to save the downloaded file.
            **kwargs: Additional arguments for the downloader.

        Returns:
            True if the download was successful, False otherwise.
        """
        pass
