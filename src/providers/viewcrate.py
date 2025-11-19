import re
from typing import Any
from urllib.parse import urljoin

from src.downloaders import DOWNLOADER_REGISTRY
from src.providers.base import BaseProvider
from src.providers.types import Episode
from src.utils import get_with_retries


class ViewCrateProvider(BaseProvider):
    """Provider for viewcrate.cc links."""

    @classmethod
    def can_handle_url(cls, url: str) -> bool:
        """Check if the provider can handle the given URL."""

        return "viewcrate.cc" in url

    def get_series_episodes(self, series_info: dict[str, Any]) -> tuple[int, list[Episode]]:
        """Finds links to new episodes for a series from a viewcrate.cc page."""

        response = get_with_retries(self.session, series_info["url"])

        html_content = response.text

        matches = re.findall(r'_raw \+= "(.*?)";', html_content)
        if not matches:
            return 0, []

        raw_data = "".join(matches)
        raw_data = raw_data.encode().decode("unicode_escape")

        found_links: list[Episode] = []

        total_episodes_in_container = 0

        last_downloaded = series_info.get("series", 0)

        episodes: dict[int, list[Episode]] = {}

        for entry in raw_data.split("\u0003"):
            if not entry:
                continue

            parts = entry.split("\u0002")

            if len(parts) != 4:
                continue

            episode_code, filename, host, link_id = parts

            episode_match: re.Match[str] | None = re.search(r"[Ss](\d+)[Ee](\d+)", episode_code)

            if not episode_match:
                continue

            season_num, episode_num = (
                int(episode_match.group(1)),
                int(episode_match.group(2)),
            )

            if episode_num not in episodes:
                episodes[episode_num] = []

            if host not in DOWNLOADER_REGISTRY:
                continue

            episodes[episode_num].append(
                Episode(
                    season=season_num,
                    episode=episode_num,
                    link=urljoin(series_info["url"], f"/get/{link_id}"),
                    filename=filename,
                    source=host,
                )
            )

        total_episodes_in_container = len(episodes)

        for episode_num in sorted(episodes.keys()):
            if episode_num <= last_downloaded:
                continue

            found_links.extend(episodes[episode_num])

        return total_episodes_in_container, sorted(found_links, key=lambda x: x.episode)

    def get_download_url(self, episode_link: str) -> str:
        """Resolves the intermediate redirect to get the final download URL."""
        # For viewcrate, the 'get' link redirects directly to the final host.
        # We can get the final URL by allowing redirects and inspecting the final URL.
        final_response = get_with_retries(self.session, episode_link, allow_redirects=True)
        return final_response.url
