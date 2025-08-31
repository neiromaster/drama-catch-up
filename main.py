import time
from src.app import run_check


def main():
    """The main entry point of the script."""
    try:
        print("🚀 Мониторинг запущен. Нажмите Ctrl+C для выхода.")
        while True:
            interval_minutes = run_check()
            print(
                f"\n---\n🕒 Проверка завершена. Следующая проверка через {interval_minutes} минут."
            )
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("\n\n🛑 Получен сигнал завершения. Выход.")


if __name__ == "__main__":
    main()
