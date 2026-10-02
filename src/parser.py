"""Разбор команд и подстановка переменных окружения."""

import os
import re
from collections.abc import Mapping


PART_PATTERN = re.compile(
    r"[^\s\"'\\]+|\\[^\n]|\"(?:[^\"\\]|\\[^\n])*\"|'[^']*'"
)
WORD_PATTERN = re.compile("(?:" + PART_PATTERN.pattern + ")+")
EXPANSION_PATTERN = re.compile(
    r"\\([^\n])|\$(?:\{([A-Za-z_][A-Za-z_0-9]*)\}"
    r"|([A-Za-z_][A-Za-z_0-9]*))"
)
DOUBLE_QUOTE_ESCAPES = frozenset('$"\\')


def expand_text(
    text: str, environment: Mapping[str, str], quoted: bool = False
) -> str:
    """Подставить переменные один раз и обработать обратную косую черту.

    Args:
        text: Часть слова без внешних кавычек.
        environment: Имена и значения переменных окружения.
        quoted: Обрабатывается ли текст внутри двойных кавычек.

    Returns:
        Текст после подстановки; неизвестные переменные дают пустую строку.
    """
    def replace(match: re.Match) -> str:
        """Заменить одну переменную или экранированный символ."""
        escaped, braced_name, plain_name = match.groups()
        if escaped is not None:
            if quoted and escaped not in DOUBLE_QUOTE_ESCAPES:
                return "\\" + escaped
            return escaped
        return environment.get(braced_name or plain_name, "")

    return EXPANSION_PATTERN.sub(replace, text)


def expand_word(word: str, environment: Mapping[str, str]) -> str:
    """Собрать слово из частей, сохранив правила одинарных кавычек."""
    parts = []
    for match in PART_PATTERN.finditer(word):
        part = match.group()
        if part.startswith("'"):
            parts.append(part[1:-1])
        elif part.startswith('"'):
            parts.append(expand_text(part[1:-1], environment, quoted=True))
        else:
            parts.append(expand_text(part, environment))
    return "".join(parts)


def parse_command(
    line: str, environment: Mapping[str, str] | None = None
) -> list[str]:
    """Разделить ввод на имя команды и аргументы.

    Args:
        line: Одна строка пользовательского ввода.
        environment: Окружение для подстановок; по умолчанию окружение ОС.

    Returns:
        Слова после подстановок. Пустая строка даёт пустой список.

    Raises:
        ValueError: Если кавычки не закрыты или строка кончается на слеш.
    """
    environment = os.environ if environment is None else environment
    words = []
    position = 0
    while position < len(line):
        if line[position].isspace():
            position += 1
            continue
        match = WORD_PATTERN.match(line, position)
        if match is None:
            message = "Незакрытая кавычка или незавершённое экранирование"
            raise ValueError(message)
        words.append(expand_word(match.group(), environment))
        position = match.end()
    return words
