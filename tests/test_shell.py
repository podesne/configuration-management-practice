"""Проверки приглашения, сеанса и продолжения работы после ошибок."""

import getpass
import io
import os
import socket
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from src.shell import Shell, build_prompt, run_repl
from src.vfs import VirtualFS


class ShellTests(unittest.TestCase):
    """Проверить приглашение и команды одного сеанса."""

    def setUp(self):
        """Создать VFS и перехватить вывод команд."""
        self.fs = VirtualFS()
        self.fs.add('docs', True, b'')
        self.fs.add('notes.txt', False, b'alpha\nalpha\nbeta\nalpha\n')
        self.output = io.StringIO()
        self.shell = Shell(self.fs, write=self.output.write)

    def test_prompt(self):
        """Данные ОС и текущий путь видны в приглашении."""
        expected = f'{getpass.getuser()}@{socket.gethostname()}:~$ '
        self.assertEqual(build_prompt(), expected)
        self.shell.execute(['cd', '/docs'])
        self.assertIn(':~/docs$ ', self.shell.prompt())
        custom = Shell(self.fs, '')
        custom.execute(['cd', '/docs'])
        self.assertEqual(custom.prompt(), '')

    def test_cd(self):
        """Переходы меняют только состояние VFS."""
        real = os.getcwd()
        self.shell.execute(['cd', 'docs'])
        self.assertEqual(self.shell.cwd, '/docs')
        self.shell.execute(['cd', '-'])
        self.assertEqual(self.shell.cwd, '/')
        self.assertEqual(self.output.getvalue(), '/\n')
        self.shell.execute(['cd'])
        for path in ('missing', 'notes.txt'):
            with self.assertRaises(ValueError):
                self.shell.execute(['cd', path])
            self.assertEqual(self.shell.cwd, '/')
        self.assertEqual(os.getcwd(), real)

    def test_exit_and_empty(self):
        """Пустая строка продолжает сеанс, exit разрешён без аргументов."""
        self.assertTrue(self.shell.execute([]))
        self.assertFalse(self.shell.execute(['exit']))
        for words in (['exit', 'now'], ['exit', ''], ['unknown']):
            with self.assertRaises(ValueError):
                self.shell.execute(words)

    def test_recovery(self):
        """Ошибки не мешают последующим командам и выходу."""
        lines = ['', 'unknown', 'ls "broken', 'exit now', 'ls', 'exit']
        errors = io.StringIO()
        with patch('builtins.input', side_effect=lines) as read:
            with redirect_stderr(errors):
                run_repl(self.shell)
        self.assertEqual(read.call_count, len(lines))
        self.assertEqual(errors.getvalue().count('Ошибка:'), 3)
        self.assertEqual(self.output.getvalue(), 'docs\nnotes.txt\n')

    def test_terminal_signals(self):
        """Конец ввода завершает программу, Ctrl+C возвращает ввод."""
        for lines in ([EOFError], [KeyboardInterrupt, 'exit']):
            with patch('builtins.input', side_effect=lines):
                with redirect_stdout(io.StringIO()):
                    run_repl(self.shell)
