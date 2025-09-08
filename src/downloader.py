import glob
import os
import shutil
import subprocess
import tempfile
import time


def download_with_yt_dlp(
    url,
    series_name,
    season,
    episode,
    output_dir,
    yt_dlp_args=None,
    retries=1,
    retry_delay=5,
):
    """Runs yt-dlp to download a video to a temporary directory,
    then moves it to the final destination, showing only the progress bar."""
    if yt_dlp_args is None:
        yt_dlp_args = []

    for attempt in range(retries):
        print(
            f"      🔽 [yt-dlp] Попытка скачивания серии {episode} (попытка {attempt + 1}/{retries})..."
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_template = os.path.join(
                temp_dir, f"{series_name} - S{season:02d}E{episode:02d}.%(ext)s"
            )

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

                print("\n      ⌛ [yt-dlp] Перемещение файла...")

                downloaded_files = glob.glob(os.path.join(temp_dir, "*"))
                if not downloaded_files:
                    print(
                        f"\n      ❌ [yt-dlp] Ошибка: скачанный файл не найден в {temp_dir}."
                    )
                    continue

                downloaded_file = downloaded_files[0]

                series_folder = os.path.join(output_dir, series_name)
                os.makedirs(series_folder, exist_ok=True)

                final_path = os.path.join(
                    series_folder, os.path.basename(downloaded_file)
                )
                shutil.move(downloaded_file, final_path)

                print(
                    f"\n      ✅ [yt-dlp] Скачивание и перемещение серии {episode} успешно завершено."
                )
                return True
            except subprocess.CalledProcessError:
                print(f"\n      ❌ [yt-dlp] Ошибка при скачивании серии {episode}.")
                if attempt < retries - 1:
                    print(f"      ▩ Повторная попытка через {retry_delay} секунд...")
                    time.sleep(retry_delay)
                continue
            except KeyboardInterrupt:
                print("\n      🛑 Скачивание прервано пользователем.")
                return False

    print(f"\n      ❌ [yt-dlp] Не удалось скачать серию {episode} после {retries} попыток.")
    return False
