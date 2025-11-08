import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup


def get_with_retries(
    session: requests.Session,
    url: str,
    retries: int = 3,
    backoff_factor: int = 5,
    timeout: int = 30,
    **kwargs: Any,
) -> requests.Response:
    """Wrapper for session.get with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                sleep_time = backoff_factor * (2**attempt)
                print(f"    ⏳ Ошибка '{e}', повторная попытка через {sleep_time} секунд...")
                time.sleep(sleep_time)
            else:
                raise e
    # This line should never be reached due to the raise in the loop, but added for type checking
    raise RuntimeError("Unexpected flow in get_with_retries")


def parse_series_links(html_content: str, series_info: dict[str, Any]) -> tuple[int, list[dict[str, Any]]]:
    """Finds links to new episodes for a series."""
    soup = BeautifulSoup(html_content, "html.parser")
    found_links: list[dict[str, Any]] = []
    total_episodes_in_container = 0
    last_downloaded = series_info.get("series", 0)

    # Using Any type for BeautifulSoup elements to avoid type checking issues
    for row in soup.find_all("tr", class_="kwj3"):
        source: str | None = None

        # Check for gofile link
        gofile_links = row.find_all("a", class_="external_link")  # type: ignore
        for link in gofile_links:  # type: ignore
            link_text = link.get_text()  # type: ignore
            if link_text and "gofile.io" in link_text.lower():
                source = "gofile"
                break

        # If no gofile link found, check for pixeldrain link
        if not source:
            pixeldrain_links = row.find_all("a", class_="external_link")  # type: ignore
            for link in pixeldrain_links:  # type: ignore
                link_text = link.get_text()  # type: ignore
                if link_text and "pixeldrain.com" in link_text.lower():
                    source = "pixeldrain"
                    break

        # If no valid source found, continue to next row
        if not source:
            continue

        title_cell = row.find("td", attrs={"title": True})  # type: ignore
        if not title_cell:
            continue

        # Accessing the 'title' attribute
        filename: str = str(title_cell.get("title", ""))  # type: ignore
        match = re.search(r"[Ss](\d+)[Ee](\d+)", filename)
        if not match:
            continue

        total_episodes_in_container += 1

        season_num, episode_num = int(match.group(1)), int(match.group(2))
        if episode_num <= last_downloaded:
            continue

        download_button = row.find("button", class_=("download", "downloaded"))  # type: ignore
        if download_button:
            data_attribute = next(
                (attr for attr in download_button.attrs if attr.startswith("data-")),  # type: ignore
                None,
            )
            if data_attribute:
                link_id = download_button.get(data_attribute)  # type: ignore
                from .constants import FILECRYPT_LINK_URL_TEMPLATE

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


def get_final_download_url(session: requests.Session, episode_link: str) -> str:
    """Resolves the intermediate redirect to get the final download URL."""
    link_page_response = get_with_retries(session, episode_link)

    js_match = re.search(r"top\.location\.href='(.*?)'", link_page_response.text)
    if not js_match:
        raise ValueError("Could not find intermediate JS redirect link.")

    intermediate_url = js_match.group(1)
    final_response = get_with_retries(session, intermediate_url, allow_redirects=True)

    return final_response.url
