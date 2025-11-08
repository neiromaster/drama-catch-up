import random
import time
import requests
import browser_cookie3
import itertools
from src.config import load_config, save_config, DEFAULT_USER_AGENT
from src.scraper import parse_series_links, get_final_download_url, get_with_retries
from src.downloader import download_with_yt_dlp, download_with_pixeldrain


def run_check():
    """Runs a single check cycle for all series."""
    config_data = load_config()
    if not config_data:
        print("❌ Файл config.yaml не найден. Пропускаю проверку.")
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
        print("⚠️ В конфиге не найдено ни одного сериала для отслеживания.")
        return settings.get("check_interval_minutes", 10)

    print("\n---")
    for i, series in enumerate(series_list):
        if i > 0:
            delay = random.randint(10, 25)
            print(f"⏸️ --- Пауза {delay} секунд перед следующим сериалом ---")
            time.sleep(delay)

        print(f"\n🎬 --- Работа с сериалом: {series['name']} ---")
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


def _handle_cookies(session, cookie_settings):
    """Handles loading cookies into the requests session."""
    if cookie_settings.get("enable", False):
        try:
            browser = cookie_settings.get("browser", "firefox")
            print(f"  🍪 Загрузка cookies из {browser}...")
            cj = getattr(browser_cookie3, browser)(domain_name="filecrypt.cc")
            session.cookies.update(cj)
            print("  ✅ Cookies успешно загружены.")
        except Exception as e:
            print(f"  ❌ Не удалось загрузить cookies: {e}")


def _process_single_series(
    series,
    config_data,
    settings,
    download_dir,
    yt_dlp_args,
    download_retries,
    download_retry_delay,
    cookie_settings,
    pixeldrain_api_key,
):
    """Processes a single series, checking for new episodes and initiating downloads."""
    with requests.Session() as session:
        session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

        _handle_cookies(session, cookie_settings)

        try:
            print(f"  📄 Загрузка страницы контейнера: {series['url']}")
            response = get_with_retries(session, series["url"])
            html_content = response.text
        except requests.RequestException as e:
            print(f"  ❌ Ошибка при загрузке страницы контейнера: {e}")
            return

        total_episodes, new_episodes = parse_series_links(html_content, series)
        if total_episodes == 0:
            print(
                "  ⚠️ На странице не найдено ни одной серии. Возможно, нужно пройти капчу."
            )
            return

        if not new_episodes:
            print("  ✅ Новых серий не найдено.")
            return

        download_delay = random.randint(5, 15)
        print(
            f"  ✨ Найдено {len(new_episodes)} уникальных ссылок на новые серии. Пауза {download_delay} секунд перед началом обработки..."
        )
        time.sleep(download_delay)

        # Group episodes by episode number
        episodes_to_download = {
            k: list(g)
            for k, g in itertools.groupby(new_episodes, key=lambda x: x["episode"])
        }

        for episode_num, links in episodes_to_download.items():
            download_successful = False
            # Sort links to prioritize gofile
            sorted_links = sorted(links, key=lambda x: x["source"] != "gofile")

            for episode_data in sorted_links:
                try:
                    print(
                        f"    🔗 Серия {episode_data['episode']} ({episode_data['source']}): обработка ссылки {episode_data['link']}"
                    )
                    final_url = get_final_download_url(session, episode_data["link"])
                    print(f"      ➡️ Финальная ссылка: {final_url}")

                    if episode_data["source"] == "gofile":
                        download_params = {
                            "url": final_url,
                            "series_name": series["name"],
                            "season": episode_data["season"],
                            "episode": episode_data["episode"],
                            "output_dir": download_dir,
                            "yt_dlp_args": yt_dlp_args,
                            "retries": download_retries,
                            "retry_delay": download_retry_delay,
                        }
                        download_successful = download_with_yt_dlp(**download_params)
                    elif episode_data["source"] == "pixeldrain":
                        download_params = {
                            "url": final_url,
                            "series_name": series["name"],
                            "season": episode_data["season"],
                            "episode": episode_data["episode"],
                            "output_dir": download_dir,
                            "retries": download_retries,
                            "retry_delay": download_retry_delay,
                            "api_key": pixeldrain_api_key,
                        }
                        download_successful = download_with_pixeldrain(
                            **download_params
                        )

                    if download_successful:
                        current_config = load_config()
                        original_series_index = next(
                            (
                                idx
                                for idx, s in enumerate(current_config["series"])
                                if s["name"] == series["name"]
                            ),
                            None,
                        )
                        if original_series_index is not None:
                            current_config["series"][original_series_index][
                                "series"
                            ] = episode_data["episode"]
                            save_config(current_config)
                            print(
                                f"      💾 Обновлен конфиг: последняя серия {episode_data['episode']}."
                            )
                        break  # Move to the next episode
                    else:
                        print(
                            f"      ⚠️ Не удалось скачать с {episode_data['source']}. Пробую следующий источник..."
                        )

                except Exception as e:
                    print(
                        f"    ❌ Ошибка при обработке серии {episode_data['episode']} с источника {episode_data['source']}: {e}"
                    )
            if not download_successful:
                print(
                    f"  ❌ Не удалось скачать серию {episode_num} со всех источников."
                )
