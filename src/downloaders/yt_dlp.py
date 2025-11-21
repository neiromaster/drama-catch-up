import glob
import os
import shutil
import subprocess
import tempfile
import time
from typing import Any

from src.downloaders.base import BaseDownloader
from src.utils import log


class YtDlpDownloader(BaseDownloader):
    """Downloader that uses yt-dlp."""

    def download(
        self,
        url: str,
        series_name: str,
        season: int,
        episode: int,
        output_dir: str,
        **kwargs: Any,
    ) -> bool:
        """Runs yt-dlp to download a video."""
        yt_dlp_args = kwargs.get("yt_dlp_args", [])
        retries = kwargs.get("retries", 3)
        retry_delay = kwargs.get("retry_delay", 5)

        for attempt in range(retries):
            log(
                f"🔽 [yt-dlp] Попытка скачивания серии {episode} (попытка {attempt + 1}/{retries})...",
                indent=3,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                output_template = os.path.join(temp_dir, f"{series_name} - S{season:02d}E{episode:02d}.%(ext)s")

                try:
                    command = (
                        [
                            "uv",
                            "run",
                            "--",
                            "yt-dlp",
                            "--output",
                            output_template,
                            "--quiet",
                            "--progress",
                        ]
                        + yt_dlp_args
                        + [url]
                    )

                    subprocess.run(command, check=True)

                    log("⌛ [yt-dlp] Перемещение файла...", indent=3, top=1)

                    downloaded_files = glob.glob(os.path.join(temp_dir, "*"))
                    if not downloaded_files:
                        log(
                            f"❌ [yt-dlp] Ошибка: скачанный файл не найден в {temp_dir}.",
                            indent=3,
                            top=1,
                        )
                        continue

                    downloaded_file = downloaded_files[0]

                    series_folder = os.path.join(output_dir, series_name)
                    os.makedirs(series_folder, exist_ok=True)

                    final_path = os.path.join(series_folder, os.path.basename(downloaded_file))
                    shutil.move(downloaded_file, final_path)

                    log(
                        f"✅ [yt-dlp] Скачивание и перемещение серии {episode} успешно завершено.",
                        indent=3,
                        top=1,
                    )
                    return True
                except subprocess.CalledProcessError:
                    log(f"❌ [yt-dlp] Ошибка при скачивании серии {episode}.", indent=2, top=1)
                    if attempt < retries - 1:
                        log(f"▩ Повторная попытка через {retry_delay} секунд...", indent=3)
                        time.sleep(retry_delay)
                    continue
                except KeyboardInterrupt:
                    log("🛑 Скачивание прервано пользователем.", indent=3, top=1)
                    raise

        log(
            f"❌ [yt-dlp] Не удалось скачать серию {episode} после {retries} попыток.",
            indent=3,
            top=1,
        )
        return False
