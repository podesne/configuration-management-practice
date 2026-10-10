"""Проверки параметров и исполнения стартового скрипта."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from src.config import parse_config
from src.main import main
from src.startup import run_script, strip_comment


class ConfigTests(unittest.TestCase):
    """Проверить настройку запуска и правила стартового скрипта."""

    def test_parameters(self):
        """Все параметры, включая пустое приглашение, сохраняются."""
        config = parse_config(['--vfs', 'a b.zip', '--prompt', '',
                               '--script', 'start.shell'])
        self.assertEqual(config.vfs, 'a b.zip')
        self.assertEqual(config.prompt, '')
        self.assertEqual(config.script, 'start.shell')
        self.assertIsNone(parse_config([]).vfs)

    def test_comments(self):
        """Хеши в кавычках и после экранирования остаются аргументами."""
        self.assertEqual(strip_comment('ls a # text'), 'ls a ')
        self.assertEqual(strip_comment('ls "#" \\#'), 'ls "#" \\#')
        self.assertEqual(strip_comment("ls '#' # text"), "ls '#' ")
        self.assertEqual(strip_comment('# text'), '')

    def test_script_exit_and_echo(self):
        """Exit останавливает скрипт; ввод и вывод видны на экране."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'start.shell'
            path.write_text('ls\nexit\nunknown\n', encoding='utf-8')
            output = io.StringIO()
            with patch('builtins.input') as read:
                with redirect_stdout(output):
                    self.assertEqual(main(['--prompt', 'x> ',
                                           '--script', str(path)]), 0)
            read.assert_not_called()
            self.assertIn('x> ls\nx> exit', output.getvalue())
            self.assertNotIn('unknown', output.getvalue())

    def test_missing_script(self):
        """Ошибка запуска возвращает ненулевой код, без REPL."""
        with tempfile.TemporaryDirectory() as directory:
            with redirect_stdout(io.StringIO()):
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(main(['--script', directory]), 1)

    def test_script_end_continues(self):
        """Конец скрипта разрешает последующий интерактивный ввод."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'start.shell'
            path.write_text('# comment\nls\n', encoding='utf-8')
            with redirect_stdout(io.StringIO()):
                self.assertTrue(run_script(str(path), lambda: '> ',
                                           lambda line: True))
