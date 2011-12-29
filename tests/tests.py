import codecs
import Image
import os
import sys
sys.path = [ "src" ] + sys.path
import tempfile

import unittest

import tesseract


class TestContext(unittest.TestCase):
    """
    These tests make sure the requirements for the tests are met.
    """
    def setUp(self):
        pass

    def test_available(self):
        self.assertTrue(tesseract.is_tesseract_available(),
                       "Tesseract not found. Is it installed ?")

    def test_version(self):
        self.assertEqual(tesseract.get_version(), (3, 0, 1),
                         ("Tesseract does not have the expected version"
                          " (3.01) ! Tests will fail !"))

    def test_langs(self):
        langs = tesseract.get_available_languages()
        self.assertTrue("eng" in langs, 
                        ("English training does not appear to be installed."
                         " (required for the tests)"))
        self.assertTrue("fra" in langs,
                        ("French training does not appear to be installed."
                         " (required for the tests)"))

    def tearDown(self):
        pass


class TestTxt(unittest.TestCase):
    """
    These tests make sure the "usual" OCR works fine. (the one generating
    a .txt file)
    """
    def setUp(self):
        pass

    def __test_txt(self, image_file, expected_output_file, lang='eng'):
        image_file = "tests/" + image_file
        expected_output_file = "tests/" + expected_output_file

        expected_output = ""
        with codecs.open(expected_output_file, 'r', encoding='utf-8') \
                as file_descriptor:
            for line in file_descriptor:
                expected_output += line
        expected_output = expected_output.strip()

        output = tesseract.image_to_string(Image.open(image_file), lang=lang)

        self.assertEqual(output, expected_output)


    def test_basic(self):
        self.__test_txt('test.png', 'test.txt')

    def test_european(self):
        self.__test_txt('test-european.jpg', 'test-european.txt')

    def test_french(self):
        self.__test_txt('test-french.jpg', 'test-french.txt', 'fra')

    def tearDown(self):
        pass


class TestBox(unittest.TestCase):
    """
    These tests make sure that Tesseract box handling works fine.
    """
    def setUp(self):
        pass

    def __test_txt(self, image_file, expected_box_file, lang='eng'):
        image_file = "tests/" + image_file
        expected_box_file = "tests/" + expected_box_file

        with codecs.open(expected_box_file, 'r', encoding='utf-8') \
                as file_descriptor:
            expected_boxes = tesseract.read_box_file(file_descriptor)
        expected_boxes.sort()

        boxes = tesseract.image_to_string(Image.open(image_file), lang=lang,
                                          boxes=True)
        boxes.sort()

        self.assertEqual(len(boxes), len(expected_boxes))

        for i in range(0, min(len(boxes), len(expected_boxes))):
            self.assertEqual(boxes[i], expected_boxes[i])

    def test_basic(self):
        self.__test_txt('test.png', 'test.box')

    def test_european(self):
        self.__test_txt('test-european.jpg', 'test-european.box')

    def test_french(self):
        self.__test_txt('test-french.jpg', 'test-french.box', 'fra')

    def test_write_read(self):
        original_boxes = tesseract.image_to_string(Image.open("tests/test.png"),
                                                   boxes=True)
        self.assertGreater(len(original_boxes), 0)

        (file_descriptor, tmp_path) = tempfile.mkstemp()
        try:
            # we must open the file with codecs.open() for utf-8 support
            os.close(file_descriptor)

            with codecs.open(tmp_path, 'w', encoding='utf-8') as file_descriptor:
                tesseract.write_box_file(file_descriptor, original_boxes)

            with codecs.open(tmp_path, 'r', encoding='utf-8') as file_descriptor:
                new_boxes = tesseract.read_box_file(file_descriptor)

            self.assertEqual(len(new_boxes), len(original_boxes))
            for i in range(0, len(original_boxes)):
                self.assertEqual(new_boxes[i], original_boxes[i])
        finally:
            os.remove(tmp_path)

    def tearDown(self):
        pass


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
    tests = unittest.TestSuite(map(TestBox, test_names))
    all_tests.addTest(tests)

    return all_tests
