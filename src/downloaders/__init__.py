from src.downloaders.base import BaseDownloader
from src.downloaders.pixeldrain import PixeldrainDownloader
from src.downloaders.yt_dlp import YtDlpDownloader

# A registry of all available downloaders
DOWNLOADER_REGISTRY: dict[str, type[BaseDownloader]] = {
    "pixeldrain": PixeldrainDownloader,
    "gofile": YtDlpDownloader,
}


def get_downloader(downloader_name: str) -> BaseDownloader:
    """
    Factory function to get a downloader instance by name.

    Args:
        downloader_name: The name of the downloader to get.

    Returns:
        An instance of the requested downloader.

    Raises:
        ValueError: If the downloader is not found in the registry.
    """
    downloader_class = DOWNLOADER_REGISTRY.get(downloader_name)
    if not downloader_class:
        raise ValueError(f"Unknown downloader: {downloader_name}")
    return downloader_class()
