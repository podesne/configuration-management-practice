"""Создание проверочных ZIP-образов из текстовых описаний."""

import base64
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


ROOT = Path(__file__).resolve().parent.parent


def make_archive(source: Path, destination: Path) -> None:
    """Сохранить каталоги, UTF-8 текст и base64 файлы описания в ZIP."""
    specification = json.loads(source.read_text(encoding="utf-8"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for directory in specification.get("directories", []):
            archive.writestr(directory.rstrip("/") + "/", b"")
        for name, text in specification.get("files", {}).items():
            archive.writestr(name, text.encode("utf-8"))
        for name, encoded in specification.get("binary", {}).items():
            archive.writestr(name, base64.b64decode(encoded, validate=True))


def main() -> None:
    """Создать все проверочные образы в examples/generated."""
    for source in sorted((ROOT / "examples").glob("*.json")):
        destination = ROOT / "examples/generated" / (source.stem + ".zip")
        make_archive(source, destination)
        print(destination.relative_to(ROOT))


if __name__ == "__main__":
    main()
