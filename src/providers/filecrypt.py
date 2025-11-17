import re
from typing import Any, cast

from bs4 import BeautifulSoup, Tag

from src.constants import FILECRYPT_LINK_URL_TEMPLATE
from src.providers.base import BaseProvider
from src.utils import get_with_retries


class FileCryptProvider(BaseProvider):
    """Provider for filecrypt.cc links."""

    @classmethod
    def can_handle_url(cls, url: str) -> bool:
        """Check if the provider can handle the given URL."""

        return "filecrypt.cc" in url

    def get_series_episodes(self, series_info: dict[str, Any]) -> tuple[int, list[dict[str, Any]]]:
        """Finds links to new episodes for a series from a filecrypt.cc page."""
        response = get_with_retries(self.session, series_info["url"])
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")
        found_links: list[dict[str, Any]] = []
        total_episodes_in_container = 0
        last_downloaded = series_info.get("series", 0)

        for row in soup.find_all("tr", class_="kwj3"):
            row = cast(Tag, row)
            source: str | None = None

            gofile_links = row.find_all("a", class_="external_link")
            for link in gofile_links:
                link = cast(Tag, link)
                link_text = link.get_text()
                if link_text and "gofile.io" in link_text.lower():
                    source = "gofile"
                    break

            if not source:
                pixeldrain_links = row.find_all("a", class_="external_link")
                for link in pixeldrain_links:
                    link = cast(Tag, link)
                    link_text = link.get_text()
                    if link_text and "pixeldrain.com" in link_text.lower():
                        source = "pixeldrain"
                        break

            if not source:
                continue

            title_cell = cast(Tag, row.find("td", attrs={"title": True}))
            if not title_cell:
                continue

            filename: str = str(title_cell.get("title", ""))
            match = re.search(r"[Ss](\d+)[Ee](\d+)", filename)
            if not match:
                continue

            total_episodes_in_container += 1

            season_num, episode_num = int(match.group(1)), int(match.group(2))
            if episode_num <= last_downloaded:
                continue

            download_button = cast(Tag, row.find("button", class_=("download", "downloaded")))
            if download_button:
                data_attribute = next(
                    (attr for attr in download_button.attrs if attr.startswith("data-")),
                    None,
                )
                if data_attribute is not None:
                    link_id = download_button.get(data_attribute)
                    filecrypt_link = FILECRYPT_LINK_URL_TEMPLATE.format(link_id=link_id)
                    found_links.append(
                        {
                            "season": season_num,
                            "episode": episode_num,
                            "link": filecrypt_link,
                            "filename": filename,
                            "source": source,
                        }
                    )
        return total_episodes_in_container, sorted(found_links, key=lambda x: x["episode"])

    def get_download_url(self, episode_link: str) -> str:
        """Resolves the intermediate redirect to get the final download URL."""
        link_page_response = get_with_retries(self.session, episode_link)

        js_match = re.search(r"top\.location\.href='(.*?)'", link_page_response.text)
        if not js_match:
            raise ValueError("Could not find intermediate JS redirect link.")

        intermediate_url = js_match.group(1)
        final_response = get_with_retries(self.session, intermediate_url, allow_redirects=True)

        return final_response.url
