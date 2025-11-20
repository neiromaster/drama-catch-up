import re
from typing import cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.downloaders import DOWNLOADER_REGISTRY
from src.providers.base import BaseProvider
from src.providers.types import Episode


class ViewCrateProvider(BaseProvider):
    """Provider for viewcrate.cc links."""

    @classmethod
    def can_handle_url(cls, url: str) -> bool:
        """Check if the provider can handle the given URL."""

        return "viewcrate.cc" in url

    def get_series_episodes(self, url: str) -> list[Episode]:
        """Finds links to all episodes for a series from a viewcrate.cc page."""

        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")

        html_content = self.page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        all_episodes: list[Episode] = []

        episode_containers = soup.find_all("div", attrs={"data-e": True})

        for container in episode_containers:
            container = cast(Tag, container)
            episode_code = container["data-e"]
            episode_match: re.Match[str] | None = re.search(r"[Ss](\d+)[Ee](\d+)", str(episode_code))

            if not episode_match:
                continue

            season_num, episode_num = (
                int(episode_match.group(1)),
                int(episode_match.group(2)),
            )

            link_containers = container.find_all("div", attrs={"data-h": True})
            for link_container in link_containers:
                link_container = cast(Tag, link_container)
                host = str(link_container["data-h"])

                if host not in DOWNLOADER_REGISTRY:
                    continue

                filename_tag = link_container.find("span")
                if not filename_tag:
                    continue
                filename = filename_tag.get_text(strip=True)

                link_tag = cast(Tag, link_container.find("a"))
                if not link_tag or not link_tag.has_attr("href"):
                    continue
                link = link_tag["href"]

                all_episodes.append(
                    Episode(
                        season=season_num,
                        episode=episode_num,
                        link=urljoin(url, str(link)),
                        filename=filename,
                        source=host,
                    )
                )

        return sorted(all_episodes, key=lambda x: x.episode)

    def get_download_url(self, episode_link: str) -> str:
        """Resolves the intermediate redirect to get the final download URL."""
        # For viewcrate, the 'get' link redirects directly to the final host.
        # We can get the final URL by allowing redirects and inspecting the final URL.
        self.page.goto(episode_link)
        return self.page.url
