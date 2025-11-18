import itertools
import random
import time
from typing import Any

import browser_cookie3  # type: ignore
import requests

from src.config import load_config, save_config
from src.constants import DEFAULT_USER_AGENT, Episode, Series
from src.downloaders import get_downloader
from src.providers import get_provider
from src.utils import log


def run_check() -> int:
    """Runs a single check cycle for all series."""
    config_data = load_config()
    if not config_data:
        log("❌ Файл config.yaml не найден. Пропускаю проверку.")
        return 10

    settings = config_data.get("settings", {})
    series_list: list[Series] = config_data.get("series", [])

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
        _process_single_series(series, settings)

    return settings.get("check_interval_minutes", 10)


def _handle_cookies(session: requests.Session, cookie_settings: dict[str, Any]) -> None:
    """Handles loading cookies into the requests session."""
    if not cookie_settings.get("enable", False):
        return
    try:
        browser = cookie_settings.get("browser", "firefox")
        log(f"🍪 Загрузка cookies из {browser}...", indent=1)
        cj = getattr(browser_cookie3, browser)(domain_name="filecrypt.cc")
        session.cookies.update(cj)  # type: ignore
        log("✅ Cookies успешно загружены.", indent=1)
    except Exception as e:
        log(f"❌ Не удалось загрузить cookies: {e}", indent=1)


def _download_episode(
    provider: Any,
    episode_data: Episode,
    series_name: str,
    settings: dict[str, Any],
) -> bool:
    """Downloads a single episode."""
    try:
        log(
            f"🔗 Серия {episode_data['episode']} ({episode_data['source']}): обработка ссылки {episode_data['link']}",
            indent=2,
        )
        final_url = provider.get_download_url(episode_data["link"])
        log(f"➡️ Финальная ссылка: {final_url}", indent=3)

        downloader = get_downloader(episode_data["source"])
        return downloader.download(
            url=final_url,
            series_name=series_name,
            season=episode_data["season"],
            episode=episode_data["episode"],
            output_dir=settings.get("download_directory", "downloads"),
            yt_dlp_args=settings.get("yt-dlp_args", []),
            retries=settings.get("download_retries", 3),
            retry_delay=settings.get("download_retry_delay", 5),
            api_key=settings.get("pixeldrain_api_key"),
        )
    except Exception as e:
        log(
            f"❌ Ошибка при обработке серии {episode_data['episode']} с источника {episode_data['source']}: {e}",
            indent=2,
        )
        return False


def _process_single_series(series: Series, settings: dict[str, Any]) -> None:
    """Processes a single series, checking for new episodes and initiating downloads."""
    with requests.Session() as session:
        session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        _handle_cookies(session, settings.get("cookies", {}))

        try:
            log(f"🔍 Автоматическое определение провайдера для URL: {series['url']}", indent=1)
            provider = get_provider(series["url"], session)
            log(f"📄 Загрузка информации о сериях с {series['url']}", indent=1)
            total_episodes, new_episodes = provider.get_series_episodes(series)
        except (requests.RequestException, ValueError) as e:
            log(f"❌ Ошибка при получении информации о сериях: {e}", indent=1)
            return

        if total_episodes == 0:
            log("⚠️ На странице не найдено ни одной серии. Возможно, нужно пройти капчу.", indent=1)
            return
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

        episodes_to_download = {k: list(g) for k, g in itertools.groupby(new_episodes, key=lambda x: x["episode"])}

        for episode_num, links in episodes_to_download.items():
            sorted_links = sorted(links, key=lambda x: x["source"] != "gofile")
            download_successful = any(
                _download_episode(provider, Episode(**episode_data), series["name"], settings)
                for episode_data in sorted_links
            )

            if download_successful:
                current_config = load_config()
                if current_config is None:
                    log("❌ Не удалось загрузить конфиг для обновления.", indent=1)
                    continue

                series_index = next(
                    (idx for idx, s in enumerate(current_config.get("series", [])) if s["name"] == series["name"]),
                    None,
                )
                if series_index is not None:
                    season_num = links[0].get("season")
                    if season_num is not None:
                        current_config["series"][series_index]["season"] = season_num
                    current_config["series"][series_index]["episode"] = episode_num
                    save_config(current_config)
                    log(f"💾 Обновлен конфиг: Сезон {season_num}, Серия {episode_num}.", indent=2, bottom=1)
            else:
                log(f"❌ Не удалось скачать серию {episode_num} со всех источников.", indent=1)
