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


def download_file(file_id, api_key=None):
    """
    Downloads a file from pixeldrain.

    :param file_id: The ID of the file to download.
    :param api_key: The API key to use for authentication.
    :return: True if download is successful, False otherwise.
    """
    download_url = f"https://pixeldrain.com/api/file/{file_id}"
    headers = {}
    if api_key:
        auth_str = f":{api_key}"
        headers["Authorization"] = (
            "Basic " + base64.b64encode(auth_str.encode()).decode()
        )
        print("      🔑 Попытка скачивания с API ключом...")
    else:
        print("      🔽 Попытка скачивания без ключа...")

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
                        progress = downloaded_size / total_size * 100
                        sys.stdout.write(
                            f"\r      [pixeldrain] {progress:.1f}% of {total_size / 1024 / 1024:.2f}MB at {speed:.1f} KB/s"
                        )
                        sys.stdout.flush()
            print("\n      ✅ Скачивание успешно завершено.")
            return True

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
                pass  # Ignore if response is not json
        return False
    except KeyboardInterrupt:
        print("\n      🛑 Скачивание прервано пользователем.")
        return False


def main():
    """Main function to run the downloader script."""
    config_data = load_config()
    api_key = None
    if config_data:
        api_key = config_data.get("settings", {}).get("pixeldrain_api_key")

    url = input("Введите ссылку на файл pixeldrain: ")
    if not url:
        print("❌ Ссылка не может быть пустой.")
        return

    file_id = url.split("/")[-1]

    if not download_file(file_id):
        if api_key:
            print("\n      Повторная попытка с использованием API ключа...")
            download_file(file_id, api_key=api_key)
        else:
            print(
                "\n      API ключ не найден в config.yaml. Невозможно повторить попытку."
            )


if __name__ == "__main__":
    main()
