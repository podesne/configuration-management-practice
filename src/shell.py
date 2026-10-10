"""Состояние сеанса, приглашение и цикл ввода команд."""

import getpass
import socket
import sys
from collections.abc import Callable

from src.commands import edge_lines, list_files, unique_lines
from src.parser import parse_command
from src.startup import strip_comment
from src.vfs import VirtualFS


MAX_CD_ARGUMENTS = 1


def build_prompt(cwd: str = "/") -> str:
    """Получить пользователя, компьютер и текущий виртуальный каталог."""
    directory = "~" if cwd == "/" else "~" + cwd
    return f"{getpass.getuser()}@{socket.gethostname()}:{directory}$ "


class Shell:
    """Сеанс с текущим каталогом VFS и заменяемой функцией вывода."""

    def __init__(
        self, filesystem: VirtualFS | None = None,
        prompt: str | None = None, write: Callable | None = None
    ) -> None:
        """Задать образ, приглашение и вывод; начать в корне VFS."""
        self.fs = filesystem if filesystem is not None else VirtualFS()
        self.custom_prompt = prompt
        self.write = sys.stdout.write if write is None else write
        self.cwd = "/"
        self.previous = "/"

    def prompt(self) -> str:
        """Получить фиксированное приглашение или путь из состояния."""
        if self.custom_prompt is not None:
            return self.custom_prompt
        return build_prompt(self.cwd)

    def change_directory(self, arguments: list[str]) -> None:
        """Перейти в каталог, корень или предыдущий каталог."""
        if len(arguments) > MAX_CD_ARGUMENTS:
            raise ValueError("cd: ожидается не более одного пути")
        path = arguments[0] if arguments else "/"
        target = self.previous if path == "-" else path
        target = self.fs.resolve(target, self.cwd)
        if not self.fs.get(target).directory:
            raise ValueError(f"Не каталог: {target}")
        self.previous, self.cwd = self.cwd, target
        if path == "-":
            self.write(target + "\n")

    def execute(self, words: list[str]) -> bool:
        """Обработать команду; False означает выход из сеанса."""
        if not words:
            return True
        command, *arguments = words
        if command == "exit":
            if arguments:
                raise ValueError("Команда exit не принимает аргументы")
            return False
        if command == "cd":
            self.change_directory(arguments)
        else:
            self.write(self.command_output(command, arguments))
        return True

    def command_output(self, command: str, arguments: list[str]) -> str:
        """Вычислить вывод команды чтения VFS."""
        if command == "ls":
            return list_files(self.fs, self.cwd, arguments)
        if command in ("head", "tail"):
            return edge_lines(command, self.fs, self.cwd, arguments)
        if command == "uniq":
            return unique_lines(self.fs, self.cwd, arguments)
        if command == "vfs-info":
            if arguments:
                raise ValueError("Команда vfs-info не принимает аргументы")
            return self.fs.describe() + "\n"
        raise ValueError(f"Неизвестная команда: {command}")

    def process(self, line: str) -> bool:
        """Разобрать ввод и вывести ошибку без остановки сеанса."""
        try:
            return self.execute(parse_command(strip_comment(line)))
        except ValueError as error:
            print(f"Ошибка: {error}", file=sys.stderr, flush=True)
            return True


def run_repl(shell: Shell | None = None) -> None:
    """Читать команды до exit или конца ввода; Ctrl+C продолжает сеанс."""
    shell = Shell() if shell is None else shell
    while True:
        try:
            line = input(shell.prompt())
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            print()
            continue
        if not shell.process(line):
            return
