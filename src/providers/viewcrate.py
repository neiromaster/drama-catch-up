import re
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
        self.page.wait_for_load_state("domcontentloaded")

        html_content = self.page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        all_episodes: list[Episode] = []

        episode_containers = soup.select("#x_r > div")

        for container in episode_containers:
            episode_code = None
            for attr in container.attrs:
                if attr.startswith("data-") and re.search(r"[Ss](\d+)[Ee](\d+)", str(container.attrs[attr])):
                    episode_code = str(container.attrs[attr])
                    break

            if not episode_code:
                continue

            episode_match: re.Match[str] | None = re.search(r"[Ss](\d+)[Ee](\d+)", str(episode_code))

            if not episode_match:
                continue

            season_num, episode_num = (
                int(episode_match.group(1)),
                int(episode_match.group(2)),
            )

            links_parent = container.find("div", class_="bg-gray-800")
            if not isinstance(links_parent, Tag):
                continue

            link_containers = links_parent.find_all("div", recursive=False)
            for link_container in link_containers:
                if not isinstance(link_container, Tag):
                    continue

                host = None
                for attr, value in link_container.attrs.items():
                    if attr.startswith("data-") and value in DOWNLOADER_REGISTRY:
                        host = str(value)
                        break

                if not host:
                    continue

                filename_tag = link_container.find("span")
                if not isinstance(filename_tag, Tag):
                    continue
                filename = filename_tag.get_text(strip=True)

                link_div = link_container.find("div", onclick=True)
                if not isinstance(link_div, Tag):
                    continue

                onclick_attr = link_div["onclick"]
                link_match = re.search(r"location.href='(.*?)'", str(onclick_attr))
                if not link_match:
                    continue
                link = link_match.group(1)

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
