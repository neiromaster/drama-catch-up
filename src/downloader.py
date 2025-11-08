import glob
import os
import shutil
import subprocess
import tempfile
import time
import requests
import base64


def _perform_pixeldrain_download(
    download_url, series_name, season, episode, output_dir, headers
):
    """Helper function to perform the actual download."""
    try:
        with requests.get(download_url, headers=headers, stream=True) as r:
            r.raise_for_status()

            content_disposition = r.headers.get("content-disposition")
            filename = f"{series_name} - S{season:02d}E{episode:02d}"
            if content_disposition:
                parts = content_disposition.split(";")
                for part in parts:
                    if part.strip().startswith("filename="):
                        filename_part = part.split("=")[1].strip()
                        filename = filename_part.strip('"')
                        break
            else:
                pass  # Fallback to constructed filename

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                total_size = int(r.headers.get("content-length", 0))
                downloaded_size = 0
                start_time = time.time()

                for chunk in r.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        elapsed_time = time.time() - start_time
                        speed = (
                            downloaded_size / elapsed_time / 1024
                            if elapsed_time > 0
                            else 0
                        )
                        progress = downloaded_size / total_size * 100
                        print(
                            f"\r      [pixeldrain] {progress:.1f}% of {total_size / 1024 / 1024:.2f}MB at {speed:.1f} KB/s",
                            end="",
                        )
                print()

        print("\n      ⌛ [pixeldrain] Перемещение файла...")
        series_folder = os.path.join(output_dir, series_name)
        os.makedirs(series_folder, exist_ok=True)
        final_path = os.path.join(series_folder, filename)
        shutil.move(temp_path, final_path)
        print(
            f"\n      ✅ [pixeldrain] Скачивание и перемещение серии {episode} успешно завершено."
        )
        return True

    except requests.exceptions.RequestException as e:
        print(f"\n      ❌ [pixeldrain] Ошибка при скачивании серии {episode}: {e}")
        if e.response and e.response.status_code == 403:
            try:
                error_data = e.response.json()
                if error_data.get("value") == "file_rate_limited_captcha_required":
                    print("      ❌ Файл требует капчу для скачивания без ключа.")
            except Exception:
                pass
        return False
    except KeyboardInterrupt:
        print("\n      🛑 Скачивание прервано пользователем.")
        return False
    finally:
        if "temp_path" in locals() and os.path.exists(temp_path):
            os.remove(temp_path)


def download_with_pixeldrain(
    url,
    series_name,
    season,
    episode,
    output_dir,
    retries=1,
    retry_delay=5,
    api_key=None,
):
    """Downloads a file from pixeldrain, trying without key first."""
    file_id = url.split("/")[-1]
    download_url = f"https://pixeldrain.com/api/file/{file_id}"

    for attempt in range(retries):
        print(
            f"      🔽 [pixeldrain] Попытка скачивания серии {episode} (попытка {attempt + 1}/{retries})..."
        )

        # 1. Try without key
        print("      Попытка #1: Скачивание без API ключа.")
        if _perform_pixeldrain_download(
            download_url, series_name, season, episode, output_dir, headers={}
        ):
            return True

        # 2. If it fails and key exists, try with key
        if api_key:
            print("\n      Попытка #2: Скачивание с API ключом.")
            auth_str = f":{api_key}"
            headers = {
                "Authorization": "Basic "
                + base64.b64encode(auth_str.encode()).decode()
            }
            if _perform_pixeldrain_download(
                download_url,
                series_name,
                season,
                episode,
                output_dir,
                headers=headers,
            ):
                return True

        if attempt < retries - 1:
            print(f"      ▩ Повторная попытка через {retry_delay} секунд...")
            time.sleep(retry_delay)

    print(
        f"\n      ❌ [pixeldrain] Не удалось скачать серию {episode} после {retries} попыток."
    )
    return False




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

    print(
        f"\n      ❌ [yt-dlp] Не удалось скачать серию {episode} после {retries} попыток."
    )
    return False
