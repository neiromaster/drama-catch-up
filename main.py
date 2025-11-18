import sys
import time
from typing import NoReturn

from src.app import run_check
from src.utils import log

if sys.platform == "win32":
    import msvcrt
else:
    import select


def wait_for_input_or_timeout(timeout_seconds: int) -> bool:
    """
    Waits for user input or a timeout, whichever comes first.

    Args:
        timeout_seconds: The timeout in seconds.

    Returns:
        True if input was received, False otherwise.
    """
    if sys.platform == "win32":
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            if msvcrt.kbhit() and msvcrt.getch() == b"\r":
                return True
            time.sleep(0.1)
        return False

    rlist, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
    if rlist:
        sys.stdin.readline()
        return True
    return False


def main() -> NoReturn:
    """The main entry point of the script."""
    try:
        log("🚀 Мониторинг запущен. Нажмите Ctrl+C для выхода.")
        log("ℹ️ Нажмите Enter, чтобы запустить проверку немедленно.")
        while True:
            interval_minutes = run_check()
            log("---", top=1)
            log(f"🕒 Проверка завершена. Следующая проверка через {interval_minutes} минут.")

            if wait_for_input_or_timeout(interval_minutes * 60):
                log("⌨️ Enter нажат. Запускаю проверку...", top=1)

    except KeyboardInterrupt:
        log("🛑 Получен сигнал завершения. Выход.", top=2)
        sys.exit(0)


if __name__ == "__main__":
    main()
