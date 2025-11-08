import time
import requests
import base64
import sys
import yaml


def load_config():
    """Loads the YAML configuration file."""
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"❌ Ошибка при загрузке config.yaml: {e}")
        return None


def perform_download_attempt(file_id, api_key=None):
    """
    Performs a single download attempt for a file from pixeldrain.
    Returns 'success', 'low_speed', or 'failed'.
    """
    download_url = f"https://pixeldrain.com/api/file/{file_id}"
    headers = {}
    if api_key:
        auth_str = f":{api_key}"
        headers["Authorization"] = (
            "Basic " + base64.b64encode(auth_str.encode()).decode()
        )

    try:
        with requests.get(download_url, headers=headers, stream=True) as r:
            r.raise_for_status()

            content_disposition = r.headers.get("content-disposition")
            filename = file_id
            if content_disposition:
                parts = content_disposition.split(";")
                for part in parts:
                    if part.strip().startswith("filename="):
                        filename_part = part.split("=")[1].strip()
                        filename = filename_part.strip('"')
                        break

            print(f"      📄 Имя файла: {filename}")

            with open(filename, "wb") as f:
                total_size = int(r.headers.get("content-length", 0))
                downloaded_size = 0
                start_time = time.time()
                speed_checked = False

                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        elapsed_time = time.time() - start_time
                        speed = (
                            downloaded_size / elapsed_time / 1024
                            if elapsed_time > 0
                            else 0
                        )

                        if not api_key and not speed_checked and elapsed_time > 5:
                            speed_checked = True
                            if speed < 1030:
                                print(
                                    "\n      ❌ Низкая скорость скачивания (< 1030 KB/s)."
                                )
                                return "low_speed"

                        progress = downloaded_size / total_size * 100
                        sys.stdout.write(
                            f"\r      [pixeldrain] {progress:.1f}% of {total_size / 1024 / 1024:.2f}MB at {speed:.1f} KB/s"
                        )
                        sys.stdout.flush()
            print("\n      ✅ Скачивание успешно завершено.")
            return "success"

    except requests.exceptions.RequestException as e:
        print(f"\n      ❌ Ошибка при скачивании: {e}")
        if e.response and e.response.status_code == 403:
            try:
                error_data = e.response.json()
                if error_data.get("value") == "file_rate_limited_captcha_required":
                    print("      ❌ Файл требует капчу для скачивания без ключа.")
                elif error_data.get("value") == "virus_detected_captcha_required":
                    print("      ❌ В файле обнаружен вирус, требуется капча.")
            except Exception:
                pass
        return "failed"
    except KeyboardInterrupt:
        print("\n      🛑 Скачивание прервано пользователем.")
        raise


def main():
    """Main function to run the downloader script."""
    config_data = load_config() or {}
    settings = config_data.get("settings", {})
    api_key = settings.get("pixeldrain_api_key")
    download_retries = settings.get("download_retries", 3)
    download_retry_delay = settings.get("download_retry_delay", 5)

    url = input("Введите ссылку на файл pixeldrain: ")
    if not url:
        print("❌ Ссылка не может быть пустой.")
        return

    file_id = url.split("/")[-1]

    # --- Phase 1: Download without API Key ---
    print("\n--- Этап 1: Скачивание без ключа ---")
    for attempt in range(download_retries):
        print(f"      Попытка {attempt + 1}/{download_retries}...")
        status = perform_download_attempt(file_id)

        if status == "success":
            return

        if status == "low_speed":
            print("      Низкая скорость. Переход к скачиванию с ключом.")
            break

        if attempt < download_retries - 1:
            print(f"      Ошибка. Повтор через {download_retry_delay} секунд...")
            time.sleep(download_retry_delay)

    # --- Phase 2: Download with API Key ---
    if not api_key:
        print("\n      ❌ Не удалось скачать файл без ключа. API ключ не найден.")
        return

    print("\n--- Этап 2: Скачивание с API ключом ---")
    for attempt in range(download_retries):
        print(f"      Попытка {attempt + 1}/{download_retries}...")
        status = perform_download_attempt(file_id, api_key=api_key)

        if status == "success":
            return

        if attempt < download_retries - 1:
            print(f"      Ошибка. Повтор через {download_retry_delay} секунд...")
            time.sleep(download_retry_delay)

    print("\n      ❌ Не удалось скачать файл после всех попыток.")


if __name__ == "__main__":
    main()
