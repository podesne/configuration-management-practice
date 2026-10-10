"""Копирование файлов и каталогов внутри VFS без записи на диск."""

import posixpath

from src.commands import command_parser
from src.vfs import Entry, VirtualFS


class CopyOperation:
    """Проверка назначения и подготовка изменений до их применения."""

    def __init__(self, fs: VirtualFS, cwd: str) -> None:
        """Задать образ и текущий каталог сеанса."""
        self.fs = fs
        self.cwd = cwd

    def destination(self, source: str, argument: str) -> str:
        """Найти каталог назначения или проверить родителя нового пути."""
        try:
            target = self.fs.resolve(argument, self.cwd)
        except ValueError:
            if not argument or argument.endswith("/"):
                raise ValueError(f"Каталог назначения не найден: {argument}")
            parent, name = posixpath.split(argument)
            parent = self.fs.resolve(parent or ".", self.cwd)
            if not self.fs.get(parent).directory or name in ("", ".", ".."):
                raise ValueError(f"Неверное назначение: {argument}")
            target = posixpath.join(parent, name)
        else:
            if self.fs.get(target).directory:
                target = posixpath.join(target, posixpath.basename(source))
        return target

    def plan(self, source: str, target: str) -> dict[str, Entry]:
        """Проверить самокопирование и конфликты типов до изменения VFS."""
        if source == "/" or target == source:
            raise ValueError("Нельзя копировать путь в себя")
        if self.fs.get(source).directory and target.startswith(source + "/"):
            raise ValueError("Нельзя копировать каталог внутрь себя")
        updates = {}
        for path, entry in self.fs.entries.items():
            if path != source and not path.startswith(source + "/"):
                continue
            destination = target + path[len(source):]
            old = self.fs.entries.get(destination)
            if old is not None and old.directory != entry.directory:
                raise ValueError(f"Конфликт типов: {destination}")
            updates[destination] = entry
        return updates


def copy(fs: VirtualFS, cwd: str, arguments: list[str]) -> None:
    """Копировать один источник, каталоги разрешить только с -r."""
    parser = command_parser("cp")
    parser.add_argument("-r", action="store_true")
    parser.add_argument("source")
    parser.add_argument("destination")
    options = parser.parse_args(arguments)
    operation = CopyOperation(fs, cwd)
    source = fs.resolve(options.source, cwd)
    if fs.get(source).directory and not options.r:
        raise ValueError("cp: для каталога нужен флаг -r")
    target = operation.destination(source, options.destination)
    updates = operation.plan(source, target)
    fs.entries.update(updates)
