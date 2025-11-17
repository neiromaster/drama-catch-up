import requests

from src.providers.base import BaseProvider
from src.providers.filecrypt import FileCryptProvider

# A registry of all available providers
PROVIDER_REGISTRY: dict[str, type[BaseProvider]] = {
    "filecrypt": FileCryptProvider,
}


def get_provider(provider_name: str, session: requests.Session) -> BaseProvider:
    """
    Factory function to get a provider instance by name.

    Args:
        provider_name: The name of the provider to get.
        session: The requests.Session to use for the provider.

    Returns:
        An instance of the requested provider.

    Raises:
        ValueError: If the provider is not found in the registry.
    """
    provider_class = PROVIDER_REGISTRY.get(provider_name)
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")
    return provider_class(session)
