import re
import time
import requests
from bs4 import BeautifulSoup


def get_with_retries(session, url, retries=3, backoff_factor=5, timeout=30, **kwargs):
    """Wrapper for session.get with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                sleep_time = backoff_factor * (2**attempt)
                print(
                    f"    ⏳ Ошибка '{e}', повторная попытка через {sleep_time} секунд..."
                )
                time.sleep(sleep_time)
            else:
                raise e


def parse_series_links(html_content, series_info):
    """Finds links to new episodes for a series."""
    soup = BeautifulSoup(html_content, "html.parser")
    found_links = []
    last_downloaded = series_info.get("series", 0)

    for row in soup.find_all("tr", class_="kwj3"):
        if not row.find(
            "a", class_="external_link", string=lambda t: t and "gofile.io" in t.lower()
        ):
            continue
        title_cell = row.find("td", title=True)
        if not title_cell:
            continue
        filename = title_cell["title"]
        match = re.search(r"[Ss](\d+)[Ee](\d+)", filename)
        if not match:
            continue

        season_num, episode_num = int(match.group(1)), int(match.group(2))
        if episode_num <= last_downloaded:
            continue

        download_button = row.find("button", class_=("download", "downloaded"))
        if download_button:
            data_attribute = next(
                (attr for attr in download_button.attrs if attr.startswith("data-")),
                None,
            )
            if data_attribute:
                link_id = download_button[data_attribute]
                filecrypt_link = f"https://filecrypt.cc/Link/{link_id}.html"
                found_links.append(
                    {
                        "season": season_num,
                        "episode": episode_num,
                        "link": filecrypt_link,
                        "filename": filename,
                    }
                )
    return sorted(found_links, key=lambda x: x["episode"])


def get_final_download_url(session, episode_link):
    """Resolves the intermediate redirect to get the final download URL."""
    link_page_response = get_with_retries(session, episode_link)

    js_match = re.search(r"top\.location\.href='(.*?)'", link_page_response.text)
    if not js_match:
        raise ValueError("Could not find intermediate JS redirect link.")

    intermediate_url = js_match.group(1)
    final_response = get_with_retries(session, intermediate_url, allow_redirects=True)

    return final_response.url
