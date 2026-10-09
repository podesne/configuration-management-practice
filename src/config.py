"""Параметры запуска консольного эмулятора."""

import argparse
from dataclasses import dataclass


@dataclass
class Config:
    """Пути к VFS и стартовому скрипту, пользовательское приглашение."""

    vfs: str | None = None
    prompt: str | None = None
    script: str | None = None


def parse_config(arguments: list[str] | None = None) -> Config:
    """Разобрать параметры запуска; None означает аргументы процесса."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки")
    parser.add_argument("--vfs", help="путь к ZIP-образу VFS")
    parser.add_argument("--prompt", help="пользовательское приглашение")
    parser.add_argument("--script", help="путь к стартовому скрипту UTF-8")
    return Config(**vars(parser.parse_args(arguments)))


def print_config(config: Config) -> None:
    """Вывести все параметры перед началом диалога."""
    print(f"VFS: {config.vfs!r}")
    print(f"Приглашение: {config.prompt!r}")
    print(f"Стартовый скрипт: {config.script!r}")
