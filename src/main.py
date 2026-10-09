"""Запуск эмулятора с параметрами и стартовым скриптом."""

import sys

from src.config import parse_config, print_config
from src.shell import build_prompt, process_line, run_repl
from src.startup import run_script


def main(arguments: list[str] | None = None) -> int:
    """Запустить скрипт и диалог; вернуть код ошибки запуска."""
    config = parse_config(arguments)
    print_config(config)
    prompt = build_prompt() if config.prompt is None else config.prompt
    try:
        if config.script and not run_script(
            config.script, lambda: prompt, process_line
        ):
            return 0
    except (OSError, UnicodeError) as error:
        print(f"Ошибка запуска: {error}", file=sys.stderr)
        return 1
    run_repl(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
