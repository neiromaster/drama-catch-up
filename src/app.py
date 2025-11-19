import itertools
import random
import time
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlparse

import browser_cookie3  # type: ignore
import requests

from src.config import load_config, save_config
from src.constants import DEFAULT_USER_AGENT, SOURCE_PRIORITY
from src.downloaders import get_downloader
from src.providers import get_provider
from src.providers.types import Episode
from src.utils import log


def run_check() -> int:
    """Runs a single check cycle for all series."""
    config_data = load_config()
    if not config_data:
        log("❌ Файл config.yaml не найден. Пропускаю проверку.")
        return 10

    settings = config_data.get("settings", {})
    download_dir = settings.get("download_directory", "downloads")
    yt_dlp_args = settings.get("yt-dlp_args", [])
    download_retries = settings.get("download_retries", 3)
    download_retry_delay = settings.get("download_retry_delay", 5)
    cookie_settings = settings.get("cookies", {"enable": False})
    pixeldrain_api_key = settings.get("pixeldrain_api_key")
    series_list = config_data.get("series", [])

    if not series_list:
        log("⚠️ В конфиге не найдено ни одного сериала для отслеживания.")
        return settings.get("check_interval_minutes", 10)

    log("---", top=1)
    for i, series in enumerate(series_list):
        if i > 0:
            delay = random.randint(10, 25)
            log(f"--- Пауза {delay} секунд перед следующим сериалом ---", indent=1)
            time.sleep(delay)

        log(f"--- Работа с сериалом: {series['name']} ---", top=1)
        _process_single_series(
            series,
            config_data,
            settings,
            download_dir,
            yt_dlp_args,
            download_retries,
            download_retry_delay,
            cookie_settings,
            pixeldrain_api_key,
        )

    return settings.get("check_interval_minutes", 10)


def _handle_cookies(
    session: requests.Session,
    cookie_settings: dict[str, Any],
    series_url: str,
) -> None:
    """Handles loading cookies into the requests session."""
    if cookie_settings.get("enable", False):
        try:
            domain = urlparse(series_url).netloc
            if not domain:
                log("⚠️ Не удалось извлечь домен из URL серии. Пропускаю загрузку cookies.", indent=1)
                return

            browser = cookie_settings.get("browser", "firefox")
            log(f"🍪 Загрузка cookies для домена '{domain}' из {browser}...", indent=1)
            cj = getattr(browser_cookie3, browser)(domain_name=domain)
            session.cookies.update(cj)  # type: ignore
            log("✅ Cookies успешно загружены.", indent=1)
        except Exception as e:
            log(f"❌ Не удалось загрузить cookies: {e}", indent=1)


def _process_single_series(
    series: dict[str, Any],
    config_data: dict[str, Any],
    settings: dict[str, Any],
    download_dir: str,
    yt_dlp_args: list[str],
    download_retries: int,
    download_retry_delay: int,
    cookie_settings: dict[str, Any],
    pixeldrain_api_key: str,
) -> None:
    """Processes a single series, checking for new episodes and initiating downloads."""
    with requests.Session() as session:
        session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

        series_url = series["url"]

        _handle_cookies(session, cookie_settings, series_url)

        try:
            log(f"🔍 Автоматическое определение провайдера для URL: {series_url}", indent=1)
            provider = get_provider(series_url, session)

            log(f"📄 Загрузка информации о сериях с {series_url}", indent=1)
            all_episodes: Sequence[Episode] = provider.get_series_episodes(series_url)

        except (requests.RequestException, ValueError) as e:
            log(f"❌ Ошибка при получении информации о сериях: {e}", indent=1)
            return

        if not all_episodes:
            log("⚠️ На странице не найдено ни одной серии. Возможно, нужно пройти капчу.", indent=1)
            return

        last_downloaded = series.get("series", 0)
        new_episodes = [e for e in all_episodes if e.episode > last_downloaded]

        if not new_episodes:
            log("✅ Новых серий не найдено.", indent=1)
            return

        download_delay = random.randint(5, 15)
        log(
            f"✨ Найдено {len(new_episodes)} уникальных ссылок на новые серии."
            f" Пауза {download_delay} секунд перед началом обработки...",
            indent=1,
        )
        time.sleep(download_delay)

        # Group episodes by episode number
        episodes_to_download = {k: list(g) for k, g in itertools.groupby(new_episodes, key=lambda x: x.episode)}

        for episode_num, links in episodes_to_download.items():
            download_successful = False
            # Sort links to prioritize gofile, then pixeldrain
            sorted_links = sorted(links, key=lambda x: SOURCE_PRIORITY.get(x.source, 2))

            for episode_data in sorted_links:
                try:
                    log(
                        f"🔗 Серия {episode_data.episode} ({episode_data.source}): "
                        f"обработка ссылки {episode_data.link}",
                        indent=2,
                    )
                    final_url = provider.get_download_url(episode_data.link)
                    log(f"➡️ Финальная ссылка: {final_url}", indent=3)

                    downloader = get_downloader(episode_data.source)
                    download_successful = downloader.download(
                        url=final_url,
                        series_name=series["name"],
                        season=episode_data.season,
                        episode=episode_data.episode,
                        output_dir=download_dir,
                        yt_dlp_args=yt_dlp_args,
                        retries=download_retries,
                        retry_delay=download_retry_delay,
                        api_key=pixeldrain_api_key,
                    )

                    if download_successful:
                        current_config = load_config()
                        if current_config is None:
                            log("❌ Не удалось загрузить конфиг для обновления.", indent=1)
                            continue
                        original_series_index = next(
                            (idx for idx, s in enumerate(current_config["series"]) if s["name"] == series["name"]),
                            None,
                        )
                        if original_series_index is not None:
                            current_config["series"][original_series_index]["series"] = episode_data.episode
                            save_config(current_config)
                            log(f"💾 Обновлен конфиг: последняя серия {episode_data.episode}.", indent=3)
                        break  # Move to the next episode
                    else:
                        log(f"⚠️ Не удалось скачать с {episode_data.source}. Пробую следующий источник...", indent=3)

                except Exception as e:
                    log(
                        f"❌ Ошибка при обработке серии {episode_data.episode} с источника {episode_data.source}: {e}",
                        indent=2,
                    )
            if not download_successful:
                log(f"❌ Не удалось скачать серию {episode_num} со всех источников.", indent=1)
