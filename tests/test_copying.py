"""Копирование файлов, деревьев и проверка исходного ZIP."""

import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from src.shell import Shell
from src.vfs import VirtualFS


class CopyTests(unittest.TestCase):
    """Проверить копии в памяти, конфликты и отсутствие записи на диск."""

    def setUp(self):
        """Создать дерево с двоичным файлом и пустым каталогом."""
        self.fs = VirtualFS()
        self.fs.add('source/nested/data', False, b'\x00\xff\x80')
        self.fs.add('source/empty', True, b'')
        self.fs.add('target', True, b'')
        self.fs.add('file', False, b'text\n')
        self.fs.add('-dash', False, b'dash')
        self.shell = Shell(self.fs, write=io.StringIO().write)

    def test_file_and_overwrite(self):
        """Файл копируется под новым именем, в каталог и поверх файла."""
        self.shell.execute(['cp', 'file', 'new'])
        self.shell.execute(['cp', 'file', 'target'])
        self.shell.execute(['cp', '--', '-dash', 'new'])
        self.assertEqual(self.fs.read('/new'), b'dash')
        self.assertEqual(self.fs.read('/target/file'), b'text\n')
        self.assertEqual(self.fs.read('/file'), b'text\n')
        self.shell.execute(['cd', '/target'])
        self.shell.execute(['cp', '../file', 'relative'])
        self.assertEqual(self.fs.read('/target/relative'), b'text\n')

    def test_recursive_copy_and_merge(self):
        """Рекурсивная копия сохраняет байты, пустые папки и старые файлы."""
        self.shell.execute(['cp', '-r', 'source', 'target'])
        self.assertEqual(self.fs.read('/target/source/nested/data'),
                         b'\x00\xff\x80')
        self.assertTrue(self.fs.get('/target/source/empty').directory)
        self.fs.add('target/source/old', False, b'old')
        self.shell.execute(['cp', '-r', 'source', 'target'])
        self.assertEqual(self.fs.read('/target/source/old'), b'old')
        self.shell.execute(['cp', '-r', 'source', 'clone'])
        self.assertEqual(self.fs.read('/clone/nested/data'), b'\x00\xff\x80')

    def test_invalid_copies_are_atomic(self):
        """Ошибка копирования не меняет дерево ни частично, ни целиком."""
        invalid = [
            ['source', 'new'], ['missing', 'new'], ['file', 'missing/new'],
            ['file', 'missing/'], ['file', 'file'], ['-r', 'source', 'source'],
            ['-r', 'source', 'source/inside'], ['-r', '/', 'target'],
            ['-r', 'source', 'file'],
        ]
        for arguments in invalid:
            before = dict(self.fs.entries)
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    self.shell.execute(['cp'] + arguments)
                self.assertEqual(self.fs.entries, before)
        self.fs.add('target/source/nested/data', True, b'')
        before = dict(self.fs.entries)
        with self.assertRaises(ValueError):
            self.shell.execute(['cp', '-r', 'source', 'target'])
        self.assertEqual(self.fs.entries, before)

    def test_zip_and_restart(self):
        """Копия не попадает на диск и исчезает после загрузки нового сеанса."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'image.zip'
            with ZipFile(path, 'w') as archive:
                archive.writestr('data', b'\x00\xff')
            digest = hashlib.sha256(path.read_bytes()).digest()
            fs = VirtualFS.load(str(path))
            Shell(fs).execute(['cp', 'data', 'copy'])
            self.assertEqual(fs.read('/copy'), b'\x00\xff')
            self.assertEqual(list(Path(directory).iterdir()), [path])
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), digest)
            self.assertNotIn('/copy', VirtualFS.load(str(path)).entries)
