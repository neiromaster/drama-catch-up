import os
import subprocess

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
