"""Проверки границ аргументов, кавычек и переменных окружения."""

import unittest
from unittest.mock import patch

from src.parser import parse_command


class ParserTests(unittest.TestCase):
    """Проверить разбор пользовательского ввода."""

    def test_empty_input(self):
        """Пустой ввод и пробелы не создают команду."""
        for line in ("", "   ", "\t"):
            with self.subTest(line=line):
                self.assertEqual(parse_command(line, {}), [])

    def test_words_and_whitespace(self):
        """Пробелы и табуляция разделяют имя и несколько аргументов."""
        self.assertEqual(parse_command(" ls\t-a  /tmp "), ["ls", "-a", "/tmp"])

    def test_real_environment(self):
        """Без второго аргумента парсер читает окружение процесса."""
        with patch.dict("os.environ", {"HOME": "/home/student"}):
            self.assertEqual(parse_command("cd $HOME"), ["cd", "/home/student"])

    def test_variable_forms_and_suffix(self):
        """Обе формы переменных раскрываются рядом с обычным текстом."""
        environment = {"HOME": "/home/student", "USER": "student"}
        self.assertEqual(
            parse_command("ls $HOME ${HOME}/docs $USER", environment),
            ["ls", "/home/student", "/home/student/docs", "student"],
        )

    def test_unknown_variable(self):
        """Неизвестная переменная заменяется пустой строкой."""
        self.assertEqual(parse_command("ls $MISSING", {}), ["ls", ""])

    def test_empty_environment_is_respected(self):
        """Явно пустое окружение не заменяется окружением реальной ОС."""
        with patch.dict("os.environ", {"HOME": "real-home"}):
            self.assertEqual(parse_command("cd $HOME", {}), ["cd", ""])

    def test_quotes_and_empty_arguments(self):
        """Кавычки сохраняют пробелы и пустые аргументы."""
        self.assertEqual(
            parse_command('ls "my folder" \'other folder\' "" \'\'', {}),
            ["ls", "my folder", "other folder", "", ""],
        )

    def test_single_and_double_quotes(self):
        """Одинарные кавычки запрещают подстановку, двойные разрешают."""
        self.assertEqual(
            parse_command('ls \'$HOME\' "$HOME"', {"HOME": "/home/user"}),
            ["ls", "$HOME", "/home/user"],
        )

    def test_adjacent_parts(self):
        """Части без пробелов образуют один аргумент."""
        self.assertEqual(parse_command('ls a"b c"\'d\'', {}), ["ls", "ab cd"])

    def test_escaped_characters(self):
        """Экранированный доллар не раскрывается; пробел остаётся в слове."""
        self.assertEqual(
            parse_command(r'ls \$HOME my\ folder "\$HOME"', {"HOME": "home"}),
            ["ls", "$HOME", "my folder", "$HOME"],
        )

    def test_backslash_in_double_quotes(self):
        """Двойные кавычки сохраняют слеш перед обычной буквой."""
        self.assertEqual(parse_command(r'ls "a\q"', {}), ["ls", r"a\q"])

    def test_values_are_not_parsed_as_commands(self):
        """Пробелы, кавычки и доллары в значении остаются частью аргумента."""
        value = 'a b "quoted" $OTHER; exit'
        self.assertEqual(parse_command("ls $VALUE", {"VALUE": value}),
                         ["ls", value])

    def test_incomplete_input(self):
        """Незакрытые кавычки и последний слеш вызывают ошибку."""
        for line in ('ls "folder', "ls 'folder", "ls folder\\"):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_command(line, {})


if __name__ == "__main__":
    unittest.main()
