import os
import codecs
import tempfile

import unittest

from pyocr import cuneiform
from . import tests_base as base


class TestContext(unittest.TestCase):
    """
    These tests make sure the requirements for the tests are met.
    """
    def setUp(self):
        pass

    def test_available(self):
        self.assertTrue(cuneiform.is_available(),
                       "cuneiform not found. Is it installed ?")

    def test_version(self):
        self.assertEqual(cuneiform.get_version(), (1, 1, 0),
                         ("cuneiform does not have the expected version"
                          " (1.1.0) ! Tests will fail !"))

    def test_langs(self):
        langs = cuneiform.get_available_languages()
        self.assertTrue("eng" in langs,
                        ("English training does not appear to be installed."
                         " (required for the tests)"))
        self.assertTrue("fra" in langs,
                        ("French training does not appear to be installed."
                         " (required for the tests)"))

    def tearDown(self):
        pass


class BaseCuneiform(base.BaseTest):
    def _path_to_img(self, image_file):
        return os.path.join(
            "tests", "input", "specific", image_file
        )

    def _path_to_out(self, expected_output_file):
        return os.path.join(
            "tests", "output", "specific", "cuneiform", expected_output_file
        )


class TestTxt(unittest.TestCase, base.BaseTestText, BaseCuneiform):
    """
    These tests make sure the "usual" OCR works fine. (the one generating
    a .txt file)
    """
    def setUp(self):
        super(TestTxt, self).setUp()
        self.tool = cuneiform
        self.set_builder()

    def test_basic(self):
        self._test_txt('test.png', 'test.txt')

    def test_european(self):
        self._test_txt('test-european.jpg', 'test-european.txt')

    def test_french(self):
        self._test_txt('test-french.jpg', 'test-french.txt', 'fra')

    def tearDown(self):
        pass


class TestDigit(base.BaseTestDigit, BaseCuneiform, unittest.TestCase):
    def setUp(self):
        super(TestDigit, self).setUp()
        self.tool = cuneiform
        self.set_builder()

    def test_digits_not_implemented(self):
        image_path = self._path_to_img("test-digits.png")
        self.assertRaises(
            NotImplementedError,
            self._read_from_img,
            image_path
        )


class TestWordBox(base.BaseTestWordBox, BaseCuneiform, unittest.TestCase):
    """
    These tests make sure that cuneiform box handling works fine.
    """
    def setUp(self):
        super(TestWordBox, self).setUp()
        self.tool = cuneiform
        self.set_builder()

    def test_basic(self):
        self._test_txt('test.png', 'test.words')

    def test_european(self):
        self._test_txt('test-european.jpg', 'test-european.words')

    def test_french(self):
        self._test_txt('test-french.jpg', 'test-french.words', 'fra')

    def test_write_read(self):
        original_boxes = self._read_from_img(
            os.path.join("tests", "input", "specific", "test.png")
        )
        self.assertTrue(len(original_boxes) > 0)

        (file_descriptor, tmp_path) = tempfile.mkstemp()
        try:
            # we must open the file with codecs.open() for utf-8 support
            os.close(file_descriptor)

            with codecs.open(tmp_path, 'w', encoding='utf-8') as file_descriptor:
                self._builder.write_file(file_descriptor, original_boxes)

            with codecs.open(tmp_path, 'r', encoding='utf-8') as file_descriptor:
                new_boxes = self._builder.read_file(file_descriptor)

            self.assertEqual(len(new_boxes), len(original_boxes))
            for i in range(0, len(original_boxes)):
                self.assertEqual(new_boxes[i], original_boxes[i])
        finally:
            os.remove(tmp_path)


class TestOrientation(unittest.TestCase):
    def test_can_detect_orientation(self):
        self.assertFalse(cuneiform.can_detect_orientation())


def get_all_tests():
    all_tests = unittest.TestSuite()

    test_names = [
        'test_available',
        'test_version',
        'test_langs',
    ]
    tests = unittest.TestSuite(map(TestContext, test_names))
    all_tests.addTest(tests)

    test_names = [
        'test_basic',
        'test_european',
        'test_french',
    ]
    tests = unittest.TestSuite(map(TestTxt, test_names))
    all_tests.addTest(tests)

    test_names = [
        'test_basic',
        'test_european',
        'test_french',
        'test_write_read',
    ]
    tests = unittest.TestSuite(map(TestWordBox, test_names))
    all_tests.addTest(tests)

    test_names = [
        'test_digits_not_implemented'
    ]
    tests = unittest.TestSuite(map(TestDigit, test_names))
    all_tests.addTest(tests)

    test_names = [
        'test_can_detect_orientation',
    ]
    tests = unittest.TestSuite(map(TestOrientation, test_names))
    all_tests.addTest(tests)

    return all_tests
