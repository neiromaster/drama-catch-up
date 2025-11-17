import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.providers.base import BaseProvider
from src.utils import get_with_retries


class ViewCrateProvider(BaseProvider):
    """Provider for viewcrate.cc links."""

    def get_series_episodes(self, series_info: dict[str, Any]) -> tuple[int, list[dict[str, Any]]]:
        """Finds links to new episodes for a series from a viewcrate.cc page."""
        response = get_with_retries(self.session, series_info["url"])
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")
        found_links: list[dict[str, Any]] = []
        total_episodes_in_container = 0
        last_downloaded = series_info.get("series", 0)

        for episode_group in soup.find_all("div", class_="episode-group"):
            episode_match = re.search(r"[Ss](\d+)[Ee](\d+)", episode_group.get("data-episode", ""))
            if not episode_match:
                continue

            total_episodes_in_container += 1
            season_num, episode_num = int(episode_match.group(1)), int(episode_match.group(2))

            if episode_num <= last_downloaded:
                continue

            for link_item in episode_group.find_all("div", class_="link-item"):
                host = link_item.get("data-host")
                if host not in ["gofile.io", "pixeldrain.com"]:
                    continue

                source = "gofile" if host == "gofile.io" else "pixeldrain"

                filename_tag = link_item.find("span", class_="text-gray-100")
                filename = filename_tag.text.strip() if filename_tag else ""

                link_tag = link_item.find("a", href=True)
                if not link_tag:
                    continue

                relative_link = link_tag["href"]
                absolute_link = urljoin(series_info["url"], relative_link)

                found_links.append(
                    {
                        "season": season_num,
                        "episode": episode_num,
                        "link": absolute_link,
                        "filename": filename,
                        "source": source,
                    }
                )

        return total_episodes_in_container, sorted(found_links, key=lambda x: x["episode"])

    def get_download_url(self, episode_link: str) -> str:
        """Resolves the intermediate redirect to get the final download URL."""
        # For viewcrate, the 'get' link redirects directly to the final host.
        # We can get the final URL by allowing redirects and inspecting the final URL.
        final_response = get_with_retries(self.session, episode_link, allow_redirects=True)
        return final_response.url
