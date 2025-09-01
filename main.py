import sys
import time
from src.app import run_check

if sys.platform == "win32":
    import msvcrt
else:
    import select


def main():
    """The main entry point of the script."""
    try:
        print("🚀 Мониторинг запущен. Нажмите Ctrl+C для выхода.")
        print("ℹ️ Нажмите Enter, чтобы запустить проверку немедленно.")
        while True:
            interval_minutes = run_check()
            print(
                f"\n---\n🕒 Проверка завершена. Следующая проверка через {interval_minutes} минут."
            )

            ready = False
            if sys.platform == "win32":
                timeout = interval_minutes * 60
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key == b"\r":
                            ready = True
                            break
                    time.sleep(0.1)
            else:
                rlist, _, _ = select.select([sys.stdin], [], [], interval_minutes * 60)
                if rlist:
                    ready = True
                    sys.stdin.readline()

            if ready:
                print("\n⌨️ Enter нажат. Запускаю проверку...")

    except KeyboardInterrupt:
        print("\n\n🛑 Получен сигнал завершения. Выход.")


if __name__ == "__main__":
    main()
