import unittest
from moose.utils import six
from moose.shortcuts import ivisit

class IvisitTestCase(unittest.TestCase):
    """
    ivisit('src')
        returns all files in path `src`

    ivisit('src', pattern='*.txt', ignorecase=False)
        returns all files matches the shell-like pattern `*.txt` in `src`,
        performs a case-insensitive comparision

    ivisit('src', 'dst')
        returns all files in `src` meanwhile new path in `dst`.

    """
    def setUp(self):
        self.test_data_path = "tests/sample_data/utils"

    # a non-iterator version to ivisit
    def visit(self, **kwargs):
        filenames = []
        for x in ivisit(self.test_data_path, **kwargs):
            filenames.append(x)
        return filenames

    def test_visit_src(self):
        self.assertEqual(len(self.visit()), 3)   # a.txt, B.txt, b/b.yaml
        self.assertEqual(
            len(self.visit(pattern="*.txt")), 2
        )    # a.txt, B.txt
        self.assertEqual(
            self.visit(pattern="*b.*"),
            ['tests/sample_data/utils/B.txt','tests/sample_data/utils/b/b.yaml',]
        )
        self.assertEqual(
            self.visit(pattern="*b.*", ignorecase=False),
            ['tests/sample_data/utils/b/b.yaml',]
        )
        self.assertEqual(
            len(self.visit(pattern=("*.txt", "*b.*"))), 3
        ) # a.txt, B.txt, b/b.yaml

    def test_visit_dst(self):
        six.assertCountEqual(
            self,
            [p[1] for p in self.visit(dst='test')],
            ['test/a.txt', 'test/B.txt', 'test/b/b.yaml'])
        six.assertCountEqual(
            self,
            [p[1] for p in self.visit(dst='')],
            ['a.txt', 'B.txt', 'b/b.yaml'])
