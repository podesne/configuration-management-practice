"""Приглашение, команды-заглушки и цикл диалога с пользователем."""

import getpass
import socket
import sys
from collections.abc import Callable

from src.parser import parse_command
from src.startup import strip_comment


STUB_COMMANDS = frozenset({"ls", "cd"})


def build_prompt() -> str:
    """Получить имя пользователя и компьютера из ОС для приглашения."""
    return f"{getpass.getuser()}@{socket.gethostname()}:~$ "


def execute_command(words: list[str], write: Callable = print) -> bool:
    """Выполнить команду и вернуть, нужно ли продолжать диалог.

    Args:
        words: Имя команды и аргументы после разбора ввода.
        write: Функция вывода результата команды.

    Returns:
        False после exit без аргументов, True после остальных команд.

    Raises:
        ValueError: Для неизвестной команды или аргументов у exit.
    """
    if not words:
        return True
    command, *arguments = words
    if command == "exit":
        if arguments:
            raise ValueError("Команда exit не принимает аргументы")
        return False
    if command not in STUB_COMMANDS:
        raise ValueError(f"Неизвестная команда: {command}")
    write(f"{command}: {arguments!r}")
    return True


def process_line(line: str) -> bool:
    """Разобрать строку, вывести ошибку и вернуть признак продолжения."""
    try:
        return execute_command(parse_command(strip_comment(line)))
    except ValueError as error:
        print(f"Ошибка: {error}", file=sys.stderr, flush=True)
        return True


def run_repl(prompt: str | None = None) -> None:
    """Читать команды до exit или конца ввода; после ошибки продолжать."""
    prompt = build_prompt() if prompt is None else prompt
    while True:
        try:
            line = input(prompt)
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            print()
            continue
        if not process_line(line):
            return
