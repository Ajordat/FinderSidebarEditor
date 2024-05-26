import finder_sidebar_editor.cli as cli
import unittest


class MyTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_something(self):
        cli.x
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
