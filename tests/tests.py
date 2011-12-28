import codecs
import Image
import sys
sys.path = [ "src" ] + sys.path

import unittest

import tesseract


class TestTxt(unittest.TestCase):
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


def get_txt_testsuite():
    tests = [
        'test_basic',
        'test_european',
        'test_french',
    ]
    return unittest.TestSuite(map(TestTxt, tests))
