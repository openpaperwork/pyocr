import codecs
import os
import tempfile

import unittest

import PIL.Image

from pyocr import builders
from pyocr import libtesseract
from pyocr import PyocrException
from . import tests_base as base


class TestContext(unittest.TestCase):
    """
    These tests make sure the requirements for the tests are met.
    """
    def setUp(self):
        pass

    def test_available(self):
        self.assertTrue(
            libtesseract.is_available(),
            "Tesseract not found."
            " Are libtesseract and libleptonica installed ? "
        )

    def test_version(self):
        self.assertTrue(
            libtesseract.get_version() in (
                (3, 2, 1),
                (3, 2, 2),
                (3, 3, 0),
                (3, 4, 0),
                (3, 4, 1),
                (3, 5, 0),
            ),
            ("Tesseract does not have the expected version")
        )

    def test_langs(self):
        langs = libtesseract.get_available_languages()
        self.assertTrue("eng" in langs,
                        ("English training does not appear to be installed."
                         " (required for the tests)"))
        self.assertTrue("fra" in langs,
                        ("French training does not appear to be installed."
                         " (required for the tests)"))
        self.assertTrue("jpn" in langs,
                        ("Japanese training does not appear to be installed."
                         " (required for the tests)"))

    def test_nolangs(self):
        tessdata_prefix = os.getenv("TESSDATA_PREFIX", "")
        os.environ['TESSDATA_PREFIX'] = '/opt/tulipe'
        try:
            langs = libtesseract.get_available_languages()
            self.assertEqual(langs, [])
        finally:
            if tessdata_prefix == "":
                os.environ['TESSDATA_PREFIX'] = ""
                os.unsetenv("TESSDATA_PREFIX")
            else:
                os.environ['TESSDATA_PREFIX'] = tessdata_prefix

    def tearDown(self):
        pass


class BaseLibtesseract(base.BaseTest):
    tool = libtesseract

    def _path_to_img(self, image_file):
        return os.path.join(
            "tests", "input", "specific", image_file
        )

    def _path_to_out(self, expected_output_file):
        return os.path.join(
            "tests", "output", "specific", "libtesseract", expected_output_file
        )


class TestTxt(base.BaseTestText, BaseLibtesseract, unittest.TestCase):
    """
    These tests make sure the "usual" OCR works fine. (the one generating
    a .txt file)
    """
    def test_basic(self):
        self._test_txt('test.png', 'test.txt')

    def test_european(self):
        self._test_txt('test-european.jpg', 'test-european.txt')

    def test_french(self):
        self._test_txt('test-french.jpg', 'test-french.txt', 'fra')

    def test_japanese(self):
        self._test_txt('test-japanese.jpg', 'test-japanese.txt', 'jpn')

    def test_nolangs(self):
        """
        Issue #51: Running OCR without any language installed causes a SIGSEGV.
        """
        tessdata_prefix = os.getenv("TESSDATA_PREFIX", "")
        os.environ['TESSDATA_PREFIX'] = '/opt/tulipe'
        try:
            with self.assertRaises(PyocrException):
                self.tool.image_to_string(
                    PIL.Image.open(self._path_to_img('test-japanese.jpg')),
                    lang='fra'
                )
        finally:
            if tessdata_prefix == "":
                os.environ['TESSDATA_PREFIX'] = ""
                os.unsetenv("TESSDATA_PREFIX")
            else:
                os.environ['TESSDATA_PREFIX'] = tessdata_prefix

    def test_nolangs2(self):
        with self.assertRaises(PyocrException):
            self.tool.image_to_string(
                PIL.Image.open(self._path_to_img('test-japanese.jpg')),
                lang='doesnotexist'
            )


class TestDigit(base.BaseTestDigit, BaseLibtesseract, unittest.TestCase):
    """
    These tests make sure that Tesseract digits handling works fine.
    """
    def test_digits(self):
        self._test_txt('test-digits.png', 'test-digits.txt')


class TestWordBox(base.BaseTestWordBox, BaseLibtesseract, unittest.TestCase):
    """
    These tests make sure that Tesseract box handling works fine.
    """
    def test_basic(self):
        self._test_txt('test.png', 'test.words')

    def test_european(self):
        self._test_txt('test-european.jpg', 'test-european.words')

    def test_french(self):
        self._test_txt('test-french.jpg', 'test-french.words', 'fra')

    def test_japanese(self):
        self._test_txt('test-japanese.jpg', 'test-japanese.words', 'jpn')

    def test_write_read(self):
        image_path = self._path_to_img("test.png")
        original_boxes = self._read_from_img(image_path)
        self.assertTrue(len(original_boxes) > 0)

        (file_descriptor, tmp_path) = tempfile.mkstemp()
        try:
            # we must open the file with codecs.open() for utf-8 support
            os.close(file_descriptor)

            with codecs.open(tmp_path, 'w', encoding='utf-8') as fdescriptor:
                self._builder.write_file(fdescriptor, original_boxes)

            with codecs.open(tmp_path, 'r', encoding='utf-8') as fdescriptor:
                new_boxes = self._builder.read_file(fdescriptor)

            self.assertEqual(len(new_boxes), len(original_boxes))
            for i in range(0, len(original_boxes)):
                self.assertEqual(new_boxes[i], original_boxes[i])
        finally:
            os.remove(tmp_path)


class TestLineBox(base.BaseTestLineBox, BaseLibtesseract, unittest.TestCase):
    """
    These tests make sure that Tesseract box handling works fine.
    """
    def test_basic(self):
        self._test_txt('test.png', 'test.lines')

    def test_european(self):
        self._test_txt('test-european.jpg', 'test-european.lines')

    def test_french(self):
        self._test_txt('test-french.jpg', 'test-french.lines', 'fra')

    def test_japanese(self):
        self._test_txt('test-japanese.jpg', 'test-japanese.lines', 'jpn')

    def test_write_read(self):
        image_path = self._path_to_img("test.png")
        original_boxes = self._read_from_img(image_path)
        self.assertTrue(len(original_boxes) > 0)

        (file_descriptor, tmp_path) = tempfile.mkstemp()
        try:
            # we must open the file with codecs.open() for utf-8 support
            os.close(file_descriptor)

            with codecs.open(tmp_path, 'w', encoding='utf-8') as fdescriptor:
                self._builder.write_file(fdescriptor, original_boxes)

            with codecs.open(tmp_path, 'r', encoding='utf-8') as fdescriptor:
                new_boxes = self._builder.read_file(fdescriptor)

            self.assertEqual(len(new_boxes), len(original_boxes))
            for i in range(0, len(original_boxes)):
                self.assertEqual(new_boxes[i], original_boxes[i])
        finally:
            os.remove(tmp_path)


class TestDigitLineBox(base.BaseTestDigitLineBox, BaseLibtesseract,
                       unittest.TestCase):
    def test_digits(self):
        self._test_txt('test-digits.png', 'test-digits.lines')


class TestOrientation(BaseLibtesseract, unittest.TestCase):
    def set_builder(self):
        self._builder = builders.TextBuilder()

    def test_can_detect_orientation(self):
        self.assertTrue(libtesseract.can_detect_orientation())

    def test_orientation_0(self):
        img = base.Image.open(self._path_to_img("test.png"))
        result = libtesseract.detect_orientation(img, lang='eng')
        self.assertEqual(result['angle'], 0)

    def test_orientation_90(self):
        img = base.Image.open(self._path_to_img("test-90.png"))
        result = libtesseract.detect_orientation(img, lang='eng')
        self.assertEqual(result['angle'], 90)


class TestBasicDoc(base.BaseTestLineBox, unittest.TestCase):
    """
    These tests make sure that Tesseract box handling works fine.
    """
    tool = libtesseract

    def _path_to_img(self, image_file):
        return os.path.join(
            "tests", "input", "real", image_file
        )

    def _path_to_out(self, expected_output_file):
        return os.path.join(
            "tests", "output", "real", "libtesseract", expected_output_file
        )

    def test_basic(self):
        self._test_txt('basic_doc.jpg', 'basic_doc.lines')


def get_all_tests():
    all_tests = unittest.TestSuite()

    test_names = [
        'test_available',
        'test_version',
        'test_langs',
        'test_nolangs',
    ]
    tests = unittest.TestSuite(map(TestContext, test_names))
    all_tests.addTest(tests)

    test_names = [
        'test_basic',
        'test_european',
        'test_french',
        'test_nolangs',
    ]
    tests = unittest.TestSuite(map(TestTxt, test_names))
    all_tests.addTest(tests)

    test_names = [
        'test_basic',
        'test_european',
        'test_french',
        'test_japanese',
        'test_write_read',
    ]
    tests = unittest.TestSuite(map(TestWordBox, test_names))
    all_tests.addTest(tests)
    tests = unittest.TestSuite(map(TestLineBox, test_names))
    all_tests.addTest(tests)

    test_names = [
        'test_digits'
    ]
    tests = unittest.TestSuite(map(TestDigit, test_names))
    all_tests.addTest(tests)
    tests = unittest.TestSuite(map(TestDigitLineBox, test_names))
    all_tests.addTest(tests)

    test_names = [
        'test_can_detect_orientation',
        'test_orientation_0',
        'test_orientation_90',
    ]
    tests = unittest.TestSuite(map(TestOrientation, test_names))
    all_tests.addTest(tests)

    test_names = [
        'test_basic',
    ]
    tests = unittest.TestSuite(map(TestBasicDoc, test_names))
    all_tests.addTest(tests)

    return all_tests
