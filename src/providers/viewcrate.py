import re
from typing import Any, cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.constants import Series
from src.providers.base import BaseProvider
from src.utils import get_with_retries


class ViewCrateProvider(BaseProvider):
    """Provider for viewcrate.cc links."""

    @classmethod
    def can_handle_url(cls, url: str) -> bool:
        """Check if the provider can handle the given URL."""

        return "viewcrate.cc" in url

    def get_series_episodes(self, series_info: Series) -> tuple[int, list[dict[str, Any]]]:
        """Finds links to new episodes for a series from a viewcrate.cc page."""
        response = get_with_retries(self.session, series_info["url"])
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")
        found_links: list[dict[str, Any]] = []
        total_episodes_in_container = 0
        last_season = series_info.get("season", 0)
        last_episode = series_info.get("episode", 0)

        for episode_group in soup.find_all("div", class_="episode-group"):
            episode_group = cast(Tag, episode_group)
            episode_match: re.Match[str] | None = re.search(
                r"[Ss](\d+)[Ee](\d+)",
                str(episode_group.get("data-episode", "")),
            )
            if not episode_match:
                continue
            assert episode_match is not None

            total_episodes_in_container += 1
            season_num, episode_num = (
                int(episode_match.group(1)),
                int(episode_match.group(2)),
            )

            if season_num < last_season or (season_num == last_season and episode_num <= last_episode):
                continue

            for link_item in episode_group.find_all("div", class_="link-item"):
                link_item = cast(Tag, link_item)
                host = link_item.get("data-host")
                if host not in ["gofile.io", "pixeldrain.com"]:
                    continue

                source = "gofile" if host == "gofile.io" else "pixeldrain"

                filename_tag = link_item.find("span", class_="text-gray-100")
                filename = filename_tag.text.strip() if filename_tag else ""

                link_tag = cast(Tag, link_item.find("a", href=True))
                if not link_tag:
                    continue

                relative_link = str(link_tag["href"])
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
