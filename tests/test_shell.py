"""Проверки команд, приглашения и продолжения диалога после ошибок."""

import getpass
import io
import socket
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

from src.shell import build_prompt, execute_command, run_repl


class ShellTests(unittest.TestCase):
    """Проверить поведение консольного прототипа."""

    def test_prompt_uses_os_data(self):
        """Приглашение совпадает с данными пользователя и компьютера ОС."""
        expected = f"{getpass.getuser()}@{socket.gethostname()}:~$ "
        self.assertEqual(build_prompt(), expected)

    def test_stubs_print_name_and_arguments(self):
        """Обе заглушки печатают все аргументы, в том числе пустой."""
        for command in ("ls", "cd"):
            with self.subTest(command=command):
                write = Mock()
                self.assertTrue(execute_command([command, "a b", ""], write))
                write.assert_called_once_with(f"{command}: ['a b', '']")

    def test_stubs_without_arguments(self):
        """Заглушки работают и без аргументов."""
        for command in ("ls", "cd"):
            write = Mock()
            self.assertTrue(execute_command([command], write))
            write.assert_called_once_with(f"{command}: []")

    def test_cd_keeps_real_directory(self):
        """Заглушка cd не меняет рабочую папку реального процесса."""
        import os

        directory = os.getcwd()
        execute_command(["cd", "/"], Mock())
        self.assertEqual(os.getcwd(), directory)

    def test_exit(self):
        """Exit завершает диалог без вывода заглушки."""
        write = Mock()
        self.assertFalse(execute_command(["exit"], write))
        write.assert_not_called()

    def test_exit_rejects_arguments(self):
        """Exit с аргументами выдаёт понятную ошибку."""
        with self.assertRaisesRegex(ValueError, "не принимает аргументы"):
            execute_command(["exit", "now"])

    def test_unknown_command(self):
        """Неизвестная команда не передаётся настоящей оболочке."""
        with self.assertRaisesRegex(ValueError, "Неизвестная команда"):
            execute_command(["rm", "-rf", "/"])

    def test_empty_command(self):
        """Пустая команда не печатает ничего и сохраняет диалог."""
        write = Mock()
        self.assertTrue(execute_command([], write))
        write.assert_not_called()

    def test_repl_recovers_from_errors(self):
        """После разных ошибок можно выполнить команду и выйти."""
        lines = ["", "unknown", 'ls "broken', "exit now", "ls", "exit"]
        output, errors = io.StringIO(), io.StringIO()
        with patch("builtins.input", side_effect=lines) as read:
            with redirect_stdout(output), redirect_stderr(errors):
                run_repl()
        self.assertEqual(read.call_count, len(lines))
        self.assertEqual(output.getvalue(), "ls: []\n")
        self.assertEqual(errors.getvalue().count("Ошибка:"), 3)

    def test_end_of_input(self):
        """Конец ввода завершает программу без ошибки."""
        with patch("builtins.input", side_effect=EOFError):
            with redirect_stdout(io.StringIO()):
                run_repl()

    def test_keyboard_interrupt(self):
        """Ctrl+C возвращает приглашение, после чего доступен exit."""
        with patch("builtins.input", side_effect=[KeyboardInterrupt, "exit"]):
            with redirect_stdout(io.StringIO()):
                run_repl()


if __name__ == "__main__":
    unittest.main()
