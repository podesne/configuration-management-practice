"""Разбор аргументов и команды чтения виртуальных файлов."""

import argparse
from itertools import groupby

from src.vfs import VirtualFS


DEFAULT_LINES = 10
SINGLE_OCCURRENCE = 1


class CommandParser(argparse.ArgumentParser):
    """Парсер команды, который не завершает весь эмулятор при ошибке."""

    def error(self, message: str) -> None:
        """Передать ошибку аргументов в основной цикл."""
        raise ValueError(f"{self.prog}: {message}")


def command_parser(name: str) -> CommandParser:
    """Создать парсер без отдельного режима справки внутри REPL."""
    return CommandParser(prog=name, add_help=False)


def line_count(value: str) -> int:
    """Разрешить только целое неотрицательное число строк."""
    if not value.isdecimal():
        raise argparse.ArgumentTypeError("N должно быть неотрицательным")
    return int(value)


def list_files(fs: VirtualFS, cwd: str, arguments: list[str]) -> str:
    """Вернуть список каталога или имя файла, с поддержкой -a."""
    parser = command_parser("ls")
    parser.add_argument("-a", action="store_true")
    parser.add_argument("path", nargs="?", default=".")
    options = parser.parse_args(arguments)
    path = fs.resolve(options.path, cwd)
    names = fs.children(path)
    if fs.get(path).directory:
        names = [name for name in names
                 if options.a or not name.startswith(".")]
        if options.a:
            names = [".", ".."] + names
    return "".join(name + "\n" for name in names)


def read_text(fs: VirtualFS, cwd: str, path: str) -> str:
    """Прочитать UTF-8 файл VFS или сообщить об ошибке кодировки."""
    name = fs.resolve(path, cwd)
    try:
        return fs.read(name).decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"Файл не в UTF-8: {name}") from error


def edge_lines(
    name: str, fs: VirtualFS, cwd: str, arguments: list[str]
) -> str:
    """Вернуть первые или последние N строк без изменения их окончаний."""
    parser = command_parser(name)
    parser.add_argument("-n", type=line_count, default=DEFAULT_LINES)
    parser.add_argument("file")
    options = parser.parse_args(arguments)
    lines = read_text(fs, cwd, options.file).splitlines(keepends=True)
    if not options.n:
        return ""
    selected = lines[:options.n] if name == "head" else lines[-options.n:]
    return "".join(selected)


def unique_lines(fs: VirtualFS, cwd: str, arguments: list[str]) -> str:
    """Обработать соседние повторы с флагами -c, -d, -u, -i."""
    parser = command_parser("uniq")
    parser.add_argument("-c", action="store_true")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("-d", action="store_true")
    selection.add_argument("-u", action="store_true")
    parser.add_argument("-i", action="store_true")
    parser.add_argument("file")
    options = parser.parse_args(arguments)
    lines = read_text(fs, cwd, options.file).splitlines(keepends=True)
    key = lambda line: line.rstrip("\r\n")
    if options.i:
        key = lambda line: line.rstrip("\r\n").casefold()
    output = []
    for _, group in groupby(lines, key):
        repeated = list(group)
        if options.d and len(repeated) == SINGLE_OCCURRENCE:
            continue
        if options.u and len(repeated) != SINGLE_OCCURRENCE:
            continue
        prefix = f"{len(repeated):7} " if options.c else ""
        output.append(prefix + repeated[0])
    return "".join(output)
