from playwright.sync_api import Page

from src.providers.base import BaseProvider
from src.providers.filecrypt import FileCryptProvider
from src.providers.viewcrate import ViewCrateProvider

# A registry of all available providers
PROVIDER_REGISTRY: list[type[BaseProvider]] = [
    FileCryptProvider,
    ViewCrateProvider,
]


def get_provider(url: str, page: Page) -> BaseProvider:
    """
    Factory function to get a provider instance based on the URL.

    Args:
        url: The URL of the series.
        page: The Playwright Page to use for the provider.

    Returns:
        An instance of the appropriate provider.

    Raises:
        ValueError: If no suitable provider is found for the given URL.
    """
    for provider_class in PROVIDER_REGISTRY:
        if provider_class.can_handle_url(url):
            return provider_class(page)
    raise ValueError(f"No suitable provider found for URL: {url}")
