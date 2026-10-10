"""Загрузка ZIP, пути, двоичные данные и неизменность образа."""

import base64
import hashlib
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile, ZipInfo

from src.vfs import VirtualFS


class VfsTests(unittest.TestCase):
    """Проверить операции в памяти и ошибки повреждённых образов."""

    def setUp(self):
        """Создать независимый образ для каждого теста."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / 'image.zip'
        with ZipFile(self.path, 'w') as archive:
            archive.writestr('a/b/c/text.txt', 'one\ntwo\n')
            archive.writestr('empty/', '')
            archive.writestr('binary', b'\x00\xff\x80')
        self.digest = hashlib.sha256(self.path.read_bytes()).digest()
        self.fs = VirtualFS.load(str(self.path))

    def test_tree_and_base64(self):
        """Каталоги восстанавливаются, двоичные байты не теряются."""
        self.assertEqual(self.fs.children('/'), ['a', 'binary', 'empty'])
        self.assertEqual(self.fs.children('/empty'), [])
        self.assertEqual(self.fs.read('/binary'), b'\x00\xff\x80')
        self.assertEqual(self.fs.entries['/binary'].data,
                         base64.b64encode(b'\x00\xff\x80').decode())
        self.assertEqual(self.fs.resolve('c/../c/text.txt', '/a/b'),
                         '/a/b/c/text.txt')
        self.assertEqual(self.fs.resolve('../../../../', '/a'), '/')
        self.assertEqual(self.fs.resolve('~/a'), '/a')

    def test_no_host_changes(self):
        """Загрузка не извлекает файлы и не меняет ZIP."""
        self.fs.describe()
        self.assertEqual(list(Path(self.temporary.name).iterdir()),
                         [self.path])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).digest(),
                         self.digest)

    def test_invalid_paths(self):
        """Файл не допускает прохода через .. или завершающий слеш."""
        for path in ('/missing', '/binary/..', '/binary/', ''):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.fs.resolve(path)
        with self.assertRaises(ValueError):
            self.fs.read('/a')

    def test_invalid_archive_entries(self):
        """Опасные имена, ссылки и повторы отклоняются."""
        for name in ('../escape', '/absolute', 'a/./b', 'a//b', 'a\\b'):
            with ZipFile(self.path, 'w') as archive:
                archive.writestr(name, 'bad')
            with self.subTest(name=name), self.assertRaises(ValueError):
                VirtualFS.load(str(self.path))
        info = ZipInfo('link')
        info.external_attr = 0o120777 << 16
        with ZipFile(self.path, 'w') as archive:
            archive.writestr(info, 'target')
        with self.assertRaises(ValueError):
            VirtualFS.load(str(self.path))

    def test_duplicates_and_conflicts(self):
        """Неоднозначные деревья не загружаются."""
        for names in (['a', 'a'], ['a', 'a/b'], ['a/b', 'a']):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                with ZipFile(self.path, 'w') as archive:
                    for name in names:
                        archive.writestr(name, 'text')
            with self.assertRaises(ValueError):
                VirtualFS.load(str(self.path))

    def test_empty_and_missing_image(self):
        """Без образа доступен только корень; неверный путь даёт ошибку."""
        self.assertEqual(VirtualFS.load(None).describe(), '/ dir')
        with self.assertRaises(OSError):
            VirtualFS.load(str(self.path) + '.missing')
