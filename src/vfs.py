"""ZIP-образ виртуальной файловой системы, хранящийся только в памяти."""

import base64
import posixpath
import stat
import zipfile
from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    """Каталог или файл с содержимым в base64."""

    directory: bool
    data: str = ""


class VirtualFS:
    """Дерево абсолютных путей; операции не изменяют исходный ZIP."""

    def __init__(self) -> None:
        """Создать пустую файловую систему с корнем."""
        self.entries = {"/": Entry(True)}

    @classmethod
    def load(cls, path: str | None) -> "VirtualFS":
        """Прочитать записи ZIP без извлечения файлов на диск."""
        filesystem = cls()
        if path is None:
            return filesystem
        with zipfile.ZipFile(path) as archive:
            names = set()
            for info in archive.infolist():
                name = validate_member(info)
                if name in names:
                    raise ValueError(f"Повторная запись ZIP: {name}")
                names.add(name)
                data = b"" if info.is_dir() else archive.read(info)
                filesystem.add(name, info.is_dir(), data)
        return filesystem

    def add(self, name: str, directory: bool, data: bytes) -> None:
        """Добавить запись образа и недостающие родительские каталоги."""
        parts = name.split("/")
        for end in range(1, len(parts)):
            parent = "/" + "/".join(parts[:end])
            if parent in self.entries and not self.entries[parent].directory:
                raise ValueError(f"Файл вместо каталога: {parent}")
            self.entries.setdefault(parent, Entry(True))
        path = "/" + name
        if path in self.entries and self.entries[path].directory != directory:
            raise ValueError(f"Конфликт типов записей: {path}")
        encoded = base64.b64encode(data).decode("ascii")
        self.entries[path] = Entry(directory, encoded)

    def resolve(self, path: str, cwd: str = "/") -> str:
        """Проверить все части абсолютного или относительного пути."""
        if not path:
            raise ValueError("Пустой путь")
        path = virtual_path(path)
        current = "/" if path.startswith("/") else cwd
        for part in path.split("/"):
            if not self.get(current).directory:
                raise ValueError(f"Не каталог: {current}")
            if part in ("", "."):
                continue
            if part == "..":
                current = posixpath.dirname(current) or "/"
            else:
                current = posixpath.join(current, part)
                self.get(current)
        return current

    def get(self, path: str) -> Entry:
        """Получить существующую запись или сообщить об ошибке пути."""
        if path not in self.entries:
            raise ValueError(f"Путь не найден: {path}")
        return self.entries[path]

    def children(self, path: str) -> list[str]:
        """Вернуть отсортированные имена непосредственных детей каталога."""
        if not self.get(path).directory:
            return [posixpath.basename(path)]
        return sorted(posixpath.basename(name) for name in self.entries
                      if name != "/" and posixpath.dirname(name) == path)

    def read(self, path: str) -> bytes:
        """Декодировать файл из base64; каталог читать нельзя."""
        entry = self.get(path)
        if entry.directory:
            raise ValueError(f"Это каталог: {path}")
        return base64.b64decode(entry.data)

    def describe(self) -> str:
        """Показать дерево, размеры файлов и их данные base64."""
        lines = []
        for path, entry in sorted(self.entries.items()):
            if entry.directory:
                lines.append(f"{path} dir")
            else:
                size = len(self.read(path))
                lines.append(f"{path} file {size} bytes base64:{entry.data}")
        return "\n".join(lines)


def validate_member(info: zipfile.ZipInfo) -> str:
    """Проверить имя и отклонить ссылки или выход за корень образа."""
    name = info.filename.rstrip("/")
    parts = name.split("/")
    unsafe = not name or info.filename.startswith("/") or "\\" in name
    if unsafe or any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"Недопустимый путь ZIP: {info.filename}")
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise ValueError(f"Символическая ссылка ZIP: {name}")
    return name


def virtual_path(path: str) -> str:
    """Заменить ~ корнем VFS; остальные пути оставить без изменения."""
    if path == "~":
        return "/"
    if path.startswith("~/"):
        return "/" + path[2:]
    return path
