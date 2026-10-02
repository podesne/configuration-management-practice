"""Точка входа для запуска через python -m src.main."""

from src.shell import run_repl


def main() -> None:
    """Запустить консольный эмулятор оболочки."""
    run_repl()


if __name__ == "__main__":
    main()
