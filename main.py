import requests
from src.config import load_config, save_config
from src.scraper import parse_series_links, get_final_download_url
from src.downloader import download_with_yt_dlp

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
                print(f"📄 Загрузка страницы контейнера: {series['url']}")
                response = session.get(series['url'], timeout=15)
                response.raise_for_status()
                html_content = response.text
            except requests.RequestException as e:
                print(f"❌ Ошибка при загрузке страницы контейнера: {e}")
                continue

            new_episodes = parse_series_links(html_content, series)
            if not new_episodes:
                print("✅ Новых серий не найдено.")
                continue

            print(f"✨ Найдено {len(new_episodes)} новых серий. Обработка...")
            for episode_data in new_episodes:
                try:
                    print(f"  🔗 Серия {episode_data['episode']}: обработка ссылки {episode_data['link']}")
                    final_url = get_final_download_url(session, episode_data['link'])

                    if "gofile.io" not in final_url:
                        print(f"    ⚠️ Конечный URL не ведет на gofile.io: {final_url}")
                        continue
                    
                    print(f"    ➡️ Финальная ссылка: {final_url}")
                    if download_with_yt_dlp(final_url, series['name'], episode_data['season'], episode_data['episode']):
                        config[i]['last'] = episode_data['episode']
                        save_config(config)
                        print(f"    💾 Обновлен конфиг: последняя серия {episode_data['episode']}.")
                    
                except Exception as e:
                    print(f"    ❌ Ошибка при обработке серии {episode_data['episode']}: {e}")

if __name__ == "__main__":
    main()
