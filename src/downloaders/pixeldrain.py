import base64
import os
import shutil
import tempfile
import time
from typing import Any, Literal

import requests

from src.constants import (
    PIXELDRAIN_API_FILE_URL,
    PIXELDRAIN_MIN_SPEED_NO_API,
    PIXELDRAIN_MIN_SPEED_WITH_API,
)
from src.downloaders.base import BaseDownloader


class PixeldrainDownloader(BaseDownloader):
    """Downloader for pixeldrain.com links."""

    def download(
        self,
        url: str,
        series_name: str,
        season: int,
        episode: int,
        output_dir: str,
        **kwargs: Any,
    ) -> bool:
        """Downloads a file from pixeldrain with a robust two-phase retry logic."""
        retries = kwargs.get("retries", 3)
        retry_delay = kwargs.get("retry_delay", 5)
        api_key = kwargs.get("api_key")

        file_id = url.split("/")[-1]
        download_url = PIXELDRAIN_API_FILE_URL.format(file_id=file_id)

        # --- Phase 1: Download without API Key ---
        print(f"      --- [pixeldrain] Этап 1: Скачивание серии {episode} без ключа ---")
        for attempt in range(retries):
            print(f"      Попытка {attempt + 1}/{retries}...")
            status = self._perform_download(download_url, series_name, season, episode, output_dir, headers={})

            if status == "success":
                return True

            if status == "low_speed":
                print("      Низкая скорость. Переход к скачиванию с ключом.")
                break

            if attempt < retries - 1:
                print(f"      Ошибка. Повтор через {retry_delay} секунд...")
                time.sleep(retry_delay)

        # --- Phase 2: Download with API Key ---
        if not api_key:
            print(f"\n      ❌ [pixeldrain] Не удалось скачать серию {episode} без ключа. API ключ не найден.")
            return False

        print(f"\n      --- [pixeldrain] Этап 2: Скачивание серии {episode} с ключом ---")
        auth_str = f":{api_key}"
        headers = {"Authorization": "Basic " + base64.b64encode(auth_str.encode()).decode()}
        for attempt in range(retries):
            print(f"      Попытка {attempt + 1}/{retries}...")
            status = self._perform_download(
                download_url,
                series_name,
                season,
                episode,
                output_dir,
                headers=headers,
            )

            if status == "success":
                return True

            if attempt < retries - 1:
                print(f"      Ошибка. Повтор через {retry_delay} секунд...")
                time.sleep(retry_delay)

        print(f"\n      ❌ [pixeldrain] Не удалось скачать серию {episode} после всех попыток.")
        return False

    def _perform_download(
        self,
        download_url: str,
        series_name: str,
        season: int,
        episode: int,
        output_dir: str,
        headers: dict[str, str],
    ) -> Literal["success", "low_speed", "failed"]:
        """
        Helper function to perform a single download attempt from pixeldrain.
        Returns 'success', 'low_speed', or 'failed'.
        """
        temp_path: str = ""
        try:
            with requests.get(download_url, headers=headers, stream=True) as r:
                r.raise_for_status()

                base_filename = f"{series_name} - S{season:02d}E{episode:02d}"
                extension = ""

                content_disposition = r.headers.get("content-disposition")
                if content_disposition:
                    parts = content_disposition.split(";")
                    for part in parts:
                        if part.strip().startswith("filename="):
                            server_filename = part.split("=")[1].strip().strip('"')
                            _, extension = os.path.splitext(server_filename)
                            break

                if not extension:
                    content_type = r.headers.get("content-type")
                    if content_type:
                        mime_map = {"video/mp4": ".mp4", "video/x-matroska": ".mkv"}
                        extension = mime_map.get(content_type.split(";")[0], "")

                filename = f"{base_filename}{extension}"

                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_path = temp_file.name
                    total_size = int(r.headers.get("content-length", 0))
                    downloaded_size = 0
                    start_time = time.time()
                    speed_checked = False

                    for chunk in r.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            elapsed_time = time.time() - start_time
                            speed = downloaded_size / elapsed_time / 1024 if elapsed_time > 0 else 0

                            if not headers and not speed_checked and elapsed_time > 5:
                                speed_checked = True
                                min_speed = (
                                    PIXELDRAIN_MIN_SPEED_NO_API if not headers else PIXELDRAIN_MIN_SPEED_WITH_API
                                )
                                if speed < min_speed:
                                    print(f"\n      ❌ [pixeldrain] Низкая скорость скачивания (< {min_speed} KB/s).")
                                    return "low_speed"

                            progress = downloaded_size / total_size * 100
                            print(
                                f"\r      [pixeldrain] {progress:.1f}% of {total_size / 1024 / 1024:.2f}MB "
                                f"at {speed:.1f} KB/s",
                                end="",
                            )
                    print()

            print("\n      ⌛ [pixeldrain] Перемещение файла...")
            series_folder = os.path.join(output_dir, series_name)
            os.makedirs(series_folder, exist_ok=True)
            final_path = os.path.join(series_folder, filename)
            shutil.move(temp_path, final_path)
            print(f"\n      ✅ [pixeldrain] Скачивание и перемещение серии {episode} успешно завершено.")
            return "success"

        except requests.exceptions.RequestException as e:
            print(f"\n      ❌ [pixeldrain] Ошибка при скачивании серии {episode}: {e}")
            if e.response and e.response.status_code == 403:
                try:
                    error_data = e.response.json()
                    if error_data.get("value") == "file_rate_limited_captcha_required":
                        print("      ❌ Файл требует капчу для скачивания без ключа.")
                except Exception:
                    pass
            return "failed"
        except KeyboardInterrupt:
            print("\n      🛑 Скачивание прервано пользователем.")
            raise
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        return "failed"
