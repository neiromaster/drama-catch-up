import re
from typing import cast

from bs4 import BeautifulSoup, Tag

from src.constants import FILECRYPT_LINK_URL_TEMPLATE
from src.downloaders import DOWNLOADER_REGISTRY
from src.providers.base import BaseProvider
from src.providers.types import Episode


class FileCryptProvider(BaseProvider):
    """Provider for filecrypt.cc links."""

    @classmethod
    def can_handle_url(cls, url: str) -> bool:
        """Check if the provider can handle the given URL."""

        return "filecrypt.cc" in url

    def get_series_episodes(self, url: str) -> list[Episode]:
        """Finds links to all episodes for a series from a filecrypt.cc page."""
        self.page.goto(url)
        html_content = self.page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        all_episodes: list[Episode] = []

        for row in soup.find_all("tr", class_="kwj3"):
            row = cast(Tag, row)
            source: str | None = None

            links = row.find_all("a", class_="external_link")
            for link in links:
                link = cast(Tag, link)
                link_text = link.get_text().lower()
                for downloader_name in DOWNLOADER_REGISTRY:
                    if downloader_name in link_text:
                        source = downloader_name
                        break
                if source:
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

            season_num, episode_num = int(match.group(1)), int(match.group(2))

            download_button = cast(Tag, row.find("button", class_=("download", "downloaded")))
            if download_button:
                data_attribute = next(
                    (attr for attr in download_button.attrs if attr.startswith("data-")),
                    None,
                )
                if data_attribute is not None:
                    link_id = download_button.get(data_attribute)
                    filecrypt_link = FILECRYPT_LINK_URL_TEMPLATE.format(link_id=link_id)
                    all_episodes.append(
                        Episode(
                            season=season_num,
                            episode=episode_num,
                            link=filecrypt_link,
                            filename=filename,
                            source=source,
                        )
                    )
        return sorted(all_episodes, key=lambda x: x.episode)

    def get_download_url(self, episode_link: str) -> str:
        """Resolves the intermediate redirect to get the final download URL."""
        self.page.goto(episode_link)
        return self.page.url
