import select
import sys
from src.app import run_check


def main():
    """The main entry point of the script."""
    try:
        print("🚀 Мониторинг запущен. Нажмите Ctrl+C для выхода.")
        print("ℹ️  Нажмите Enter, чтобы запустить проверку немедленно.")
        while True:
            interval_minutes = run_check()
            print(
                f"\n---\n🕒 Проверка завершена. Следующая проверка через {interval_minutes} минут."
            )

            ready, _, _ = select.select([sys.stdin], [], [], interval_minutes * 60)

            if ready:
                print("\n⌨️ Enter нажат. Запускаю проверку...")

    except KeyboardInterrupt:
        print("\n\n🛑 Получен сигнал завершения. Выход.")


if __name__ == "__main__":
    main()
