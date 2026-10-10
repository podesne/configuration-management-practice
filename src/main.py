"""Запуск эмулятора с параметрами и стартовым скриптом."""

import sys
import zipfile

from src.config import parse_config, print_config
from src.shell import build_prompt, process_line, run_repl
from src.startup import run_script
from src.vfs import VirtualFS


def main(arguments: list[str] | None = None) -> int:
    """Запустить скрипт и диалог; вернуть код ошибки запуска."""
    config = parse_config(arguments)
    print_config(config)
    prompt = build_prompt() if config.prompt is None else config.prompt
    try:
        filesystem = VirtualFS.load(config.vfs)
        execute = lambda line: process_line(line, filesystem)
        if config.script and not run_script(
            config.script, lambda: prompt, execute
        ):
            return 0
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile,
            RuntimeError, NotImplementedError) as error:
        print(f"Ошибка запуска: {error}", file=sys.stderr)
        return 1
    run_repl(prompt, filesystem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
