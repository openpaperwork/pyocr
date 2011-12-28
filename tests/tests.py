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


class TestBox(unittest.TestCase):
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

    def tearDown(self):
        pass


def get_all_tests():
    all_tests = unittest.TestSuite()

    test_names = [
        'test_basic',
        'test_european',
        'test_french',
    ]
    tests = unittest.TestSuite(map(TestTxt, test_names))
    all_tests.addTest(tests)

    tests = unittest.TestSuite(map(TestBox, test_names))
    all_tests.addTest(tests)

    return all_tests
