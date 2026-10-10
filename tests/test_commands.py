"""Проверки списка файлов, границ строк и соседних повторений."""

import io
import unittest

from src.shell import Shell
from src.vfs import VirtualFS


class CommandTests(unittest.TestCase):
    """Проверить результат команд и некорректные аргументы."""

    def setUp(self):
        """Подготовить файлы с повторами, пустой и двоичный файл."""
        fs = VirtualFS()
        for name, data in {
            'notes': b'alpha\nalpha\nbeta\nalpha\n',
            'case': b'Alpha\nalpha\nBETA\n', 'empty': b'',
            'last': b'no newline', 'binary': b'\xff',
            '.hidden': b'x', '-dash': b'x',
        }.items():
            fs.add(name, False, data)
        fs.add('docs/space name', False, b'one\r\ntwo\r\nlast')
        self.output = io.StringIO()
        self.shell = Shell(fs, write=self.output.write)

    def run_command(self, words):
        """Выполнить команду и вернуть только её вывод."""
        self.output.seek(0)
        self.output.truncate()
        self.shell.execute(words)
        return self.output.getvalue()

    def test_ls(self):
        """Скрытые имена, каталог, файл и -- разбираются корректно."""
        self.assertNotIn('.hidden', self.run_command(['ls']))
        self.assertIn('.hidden', self.run_command(['ls', '-a']))
        self.assertTrue(self.run_command(['ls', '-a']).startswith('.\n..\n'))
        self.assertEqual(self.run_command(['ls', 'docs']), 'space name\n')
        self.assertEqual(self.run_command(['ls', '--', '-dash']), '-dash\n')
        with self.assertRaises(ValueError):
            self.shell.execute(['ls', '-z'])

    def test_head_tail(self):
        """Нулевой счётчик, короткие файлы и окончания строк сохраняются."""
        self.assertEqual(self.run_command(['head', '-n', '2', 'notes']),
                         'alpha\nalpha\n')
        self.assertEqual(self.run_command(['tail', '-n', '2', 'notes']),
                         'beta\nalpha\n')
        for command in ('head', 'tail'):
            self.assertEqual(self.run_command([command, '-n0', 'notes']), '')
            self.assertEqual(self.run_command([command, 'empty']), '')
            self.assertEqual(self.run_command([command, 'last']), 'no newline')
            for value in ('-1', 'x', '+2'):
                with self.assertRaises(ValueError):
                    self.shell.execute([command, '-n', value, 'notes'])
        self.assertEqual(self.run_command(['head', 'docs/space name']),
                         'one\r\ntwo\r\nlast')

    def test_uniq(self):
        """Удаляются только соседние повторы; флаги меняют отбор."""
        self.assertEqual(self.run_command(['uniq', 'notes']),
                         'alpha\nbeta\nalpha\n')
        self.assertEqual(self.run_command(['uniq', '-d', 'notes']), 'alpha\n')
        self.assertEqual(self.run_command(['uniq', '-u', 'notes']),
                         'beta\nalpha\n')
        self.assertEqual(self.run_command(['uniq', '-i', 'case']),
                         'Alpha\nBETA\n')
        self.assertEqual(self.run_command(['uniq', '-c', '-d', 'notes']),
                         '      2 alpha\n')
        self.assertEqual(self.run_command(['uniq', 'empty']), '')
        self.assertEqual(self.run_command(['uniq', 'last']), 'no newline')
        with self.assertRaises(ValueError):
            self.shell.execute(['uniq', '-d', '-u', 'notes'])

    def test_errors(self):
        """Каталоги, двоичные файлы и отсутствующие аргументы дают ошибки."""
        for command in ('head', 'tail', 'uniq'):
            for path in ('docs', 'binary', 'missing'):
                with self.subTest(command=command, path=path):
                    with self.assertRaises(ValueError):
                        self.shell.execute([command, path])
            with self.assertRaises(ValueError):
                self.shell.execute([command])
