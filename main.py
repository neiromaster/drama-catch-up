import re
import os
import yaml
import requests
import subprocess
from bs4 import BeautifulSoup

def load_config(path="config.yaml"):
    """Loads the configuration from a YAML file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return None

def save_config(data, path="config.yaml"):
    """Saves the data to a YAML file."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)

def parse_links(html_content, series_info):
    """Finds links to gofile.io and their corresponding download buttons."""
    soup = BeautifulSoup(html_content, "html.parser")
    found_links = []
    last_downloaded = series_info.get("last", 0)

    for row in soup.find_all("tr", class_="kwj3"):
        if not row.find("a", class_="external_link", string=lambda t: t and "gofile.io" in t.lower()):
            continue
        title_cell = row.find("td", title=True)
        if not title_cell: continue
        filename = title_cell["title"]
        match = re.search(r"[Ss](\d+)[Ee](\d+)", filename)
        if not match: continue
        
        season_num, episode_num = int(match.group(1)), int(match.group(2))
        if episode_num <= last_downloaded:
            continue

        download_button = row.find("button", class_=("download", "downloaded"))
        if download_button:
            data_attribute = next((attr for attr in download_button.attrs if attr.startswith("data-")), None)
            if data_attribute:
                link_id = download_button[data_attribute]
                filecrypt_link = f"https://filecrypt.cc/Link/{link_id}.html"
                found_links.append({
                    "season": season_num,
                    "episode": episode_num,
                    "link": filecrypt_link,
                    "filename": filename
                })
    return sorted(found_links, key=lambda x: x['episode'])

def download_with_yt_dlp(url, series_name, season, episode, output_dir="downloads"):
    """Runs yt-dlp to download a video."""
    print(f"  🔽 [yt-dlp] Попытка скачивания серии {episode}...")
    series_folder = os.path.join(output_dir, series_name)
    os.makedirs(series_folder, exist_ok=True)
    
    output_template = f"{series_folder}/{series_name} - S{season:02d}E{episode:02d}.%(ext)s"

    try:
        command = ["uv", "run", "--", "yt-dlp", "--output", output_template, url]
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print(f"  ✅ [yt-dlp] Скачивание серии {episode} успешно завершено.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ [yt-dlp] Ошибка при скачивании серии {episode}.")
        print(e.stderr)
        return False

def main():
    """The main function of the script."""
    config = load_config()
    if not config:
        print("❌ Файл config.yaml не найден. Выход.")
        return

    for i, series in enumerate(config):
        print(f"\n🎬 --- Работа с сериалом: {series['name']} ---")
        
        with requests.Session() as session:
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
            })

            try:
                response = session.get(series['url'], timeout=15)
                response.raise_for_status()
                html_content = response.text
            except requests.RequestException as e:
                print(f"❌ Ошибка при загрузке страницы контейнера: {e}")
                continue

            new_episodes = parse_links(html_content, series)
            if not new_episodes:
                print("✅ Новых серий не найдено.")
                continue

            print(f"✨ Найдено {len(new_episodes)} новых серий. Обработка...")
            for episode_data in new_episodes:
                try:
                    print(f"  🔗 Серия {episode_data['episode']}: обработка ссылки {episode_data['link']}")
                    link_page_response = session.get(episode_data['link'], timeout=15)
                    link_page_response.raise_for_status()

                    js_match = re.search(r"top.location.href='(.*?)'", link_page_response.text)
                    if not js_match:
                        print("    ⚠️ Не удалось найти промежуточную ссылку в JavaScript.")
                        continue
                    
                    intermediate_url = js_match.group(1)
                    final_response = session.get(intermediate_url, allow_redirects=True, timeout=15)
                    final_response.raise_for_status()
                    final_url = final_response.url

                    if "gofile.io" not in final_url:
                        print(f"    ⚠️ Конечный URL не ведет на gofile.io: {final_url}")
                        continue
                    
                    print(f"    ➡️  Финальная ссылка: {final_url}")
                    if download_with_yt_dlp(final_url, series['name'], episode_data['season'], episode_data['episode']):
                        config[i]['last'] = episode_data['episode']
                        save_config(config)
                        print(f"    💾 Обновлен конфиг: последняя серия {episode_data['episode']}.")
                    
                except requests.RequestException as e:
                    print(f"    ❌ Ошибка при обработке серии {episode_data['episode']}: {e}")
                except Exception as e:
                    print(f"    ❌ Непредвиденная ошибка: {e}")

if __name__ == "__main__":
    main()