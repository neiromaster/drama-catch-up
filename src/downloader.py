import os
import subprocess

def download_with_yt_dlp(url, series_name, season, episode, output_dir, yt_dlp_args=None):
    """Runs yt-dlp to download a video, showing progress in real-time."""
    if yt_dlp_args is None:
        yt_dlp_args = []

    print(f"  🔽 [yt-dlp] Попытка скачивания серии {episode}...")
    series_folder = os.path.join(output_dir, series_name)
    os.makedirs(series_folder, exist_ok=True)
    
    output_template = f"{series_folder}/{series_name} - S{season:02d}E{episode:02d}.%(ext)s"

    try:
        command = [
            "uv", "run", "--", "yt-dlp",
            "--output", output_template
        ] + yt_dlp_args + [url]

        subprocess.run(command, check=True)
        
        print(f"  ✅ [yt-dlp] Скачивание серии {episode} успешно завершено.")
        return True
    except subprocess.CalledProcessError:
        print(f"  ❌ [yt-dlp] Ошибка при скачивании серии {episode}.")
        return False
    except KeyboardInterrupt:
        print("\n  🛑 Скачивание прервано пользователем.")
        return False