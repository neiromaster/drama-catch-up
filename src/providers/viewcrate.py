import re

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
        # Give the page time to run its JavaScript
        self.page.wait_for_timeout(10000)

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

                link_div = link_container.find("div", {"role": "button", "data-z": True})
                if not isinstance(link_div, Tag):
                    continue

                # The link is now the data-z attribute
                link_data_z = link_div.get("data-z")
                if not link_data_z:
                    continue

                # If data-z is a list, take the first element
                if isinstance(link_data_z, list):
                    link_data_z = link_data_z[0]

                all_episodes.append(
                    Episode(
                        season=season_num,
                        episode=episode_num,
                        link=str(link_data_z),  # Store the data-z value
                        filename=filename,
                        source=host,
                    )
                )

        return sorted(all_episodes, key=lambda x: x.episode)

    def get_download_url(self, episode_link: str) -> str:
        """
        Resolves the intermediate redirect by clicking the button corresponding
        to the episode_link (which is a data-z value).
        """
        # The episode_link is the data-z attribute
        button_selector = f"div[role='button'][data-z='{episode_link}']"

        button = self.page.locator(button_selector).first
        if button.count() == 0:
            raise ValueError(f"Could not find download button with selector: {button_selector}")

        # Remove potential overlays before clicking
        self.page.evaluate(
            "() => { document.querySelectorAll('iframe[style*=\"z-index: 2147483647\"]').forEach(e => e.remove()); }"
        )

        # Force click to bypass any overlays
        button.click(force=True, timeout=10000)

        # Wait for the new page to load after the click
        self.page.wait_for_load_state("domcontentloaded")

        return self.page.url
