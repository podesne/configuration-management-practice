"""Запуск эмулятора с параметрами и стартовым скриптом."""

import sys
import zipfile

from src.config import parse_config, print_config
from src.shell import Shell, run_repl
from src.startup import run_script
from src.vfs import VirtualFS


def main(arguments: list[str] | None = None) -> int:
    """Запустить скрипт и диалог; вернуть код ошибки запуска."""
    config = parse_config(arguments)
    print_config(config)
    try:
        filesystem = VirtualFS.load(config.vfs)
        shell = Shell(filesystem, config.prompt)
        if config.script and not run_script(
            config.script, shell.prompt, shell.process
        ):
            return 0
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile,
            RuntimeError, NotImplementedError) as error:
        print(f"Ошибка запуска: {error}", file=sys.stderr)
        return 1
    run_repl(shell)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
