import re
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

    def get_series_episodes(self, url: str) -> list[Episode]:
        """Finds links to all episodes for a series from a viewcrate.cc page."""

        response = get_with_retries(self.session, url)

        html_content = response.text

        matches = re.findall(r'_raw \+= "(.*?)";', html_content)
        if not matches:
            return []

        raw_data = "".join(matches)
        raw_data = raw_data.encode().decode("unicode_escape")

        all_episodes: list[Episode] = []

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

            if host not in DOWNLOADER_REGISTRY:
                continue

            all_episodes.append(
                Episode(
                    season=season_num,
                    episode=episode_num,
                    link=urljoin(url, f"/get/{link_id}"),
                    filename=filename,
                    source=host,
                )
            )

        return sorted(all_episodes, key=lambda x: x.episode)

    def get_download_url(self, episode_link: str) -> str:
        """Resolves the intermediate redirect to get the final download URL."""
        # For viewcrate, the 'get' link redirects directly to the final host.
        # We can get the final URL by allowing redirects and inspecting the final URL.
        final_response = get_with_retries(self.session, episode_link, allow_redirects=True)
        return final_response.url
