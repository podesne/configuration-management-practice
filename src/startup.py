"""Комментарии и выполнение стартового скрипта."""

from collections.abc import Callable
from pathlib import Path


def strip_comment(line: str) -> str:
    """Удалить комментарий Python с # вне кавычек и экранирования."""
    quote = None
    escaped = False
    for position, character in enumerate(line):
        if escaped:
            escaped = False
        elif character == "\\" and quote != "'":
            escaped = True
        elif quote:
            if character == quote:
                quote = None
        elif character in "\"'":
            quote = character
        elif character == "#":
            return line[:position]
    return line


def run_script(path: str, prompt: Callable, execute: Callable) -> bool:
    """Показать строки UTF-8 скрипта и выполнить их до exit или конца."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for line in lines:
        print(f"{prompt()}{line}", flush=True)
        if not execute(strip_comment(line)):
            return False
    return True
