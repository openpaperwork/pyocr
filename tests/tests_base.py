import codecs
from PIL import Image
import sys
sys.path = ["src"] + sys.path

import six

from pyocr import builders
from pyocr import tesseract


class BaseTest(object):
    tool = None

    def _path_to_img(self, image_file):
        raise NotImplementedError("Implement in subclasses.")

    def _path_to_out(self, expected_output_file):
        raise NotImplementedError("Implement in subclasses.")

    def _read_from_expected(self, expected_output_path):
        raise NotImplementedError("Implement in subclasses.")

    def _read_from_img(self, image_path, lang=None):
        return self.tool.image_to_string(
            Image.open(image_path),
            lang=lang,
            builder=self._builder
        )

    def _test_equal(self, output, expected_output):
        raise NotImplementedError("Implement in subclasses.")

    def set_builder(self):
        raise NotImplementedError("Implemented in subclasses.")

    def setUp(self):
        self.set_builder()

    def _test_txt(self, image_file, expected_output_file, lang='eng'):
        image_path = self._path_to_img(image_file)
        expected_output_path = self._path_to_out(expected_output_file)

        expected_output = self._read_from_expected(expected_output_path)
        output = self._read_from_img(image_path, lang)

        self._test_equal(output, expected_output)


class BaseTestText(BaseTest):
    def set_builder(self):
        self._builder = builders.TextBuilder()

    def _read_from_expected(self, expected_output_path):
        with codecs.open(expected_output_path, 'r', encoding='utf-8') \
                as file_descriptor:
            return file_descriptor.read().strip()

    def _test_equal(self, output, expected_output):
        self.assertEqual(output, expected_output)


class BaseTestDigit(BaseTestText):
    def set_builder(self):
        self._builder = builders.DigitBuilder()


class BaseTestBox(BaseTest):
    def _read_from_expected(self, expected_output_path):
        with codecs.open(expected_output_path, 'r', encoding='utf-8') \
                as file_descriptor:
            expected_boxes = self._builder.read_file(file_descriptor)
        expected_boxes.sort()

        return expected_boxes

    def _read_from_img(self, image_path, lang=None):
        boxes = tesseract.image_to_string(
            Image.open(image_path),
            lang=lang,
            builder=self._builder
        )
        boxes.sort()

        return boxes


class BaseTestWordBox(BaseTestBox):
    def set_builder(self):
        self._builder = builders.WordBoxBuilder()

    def _test_equal(self, output, expected_output):
        self.assertTrue(len(output) > 0)
        self.assertEqual(len(output), len(expected_output))

        for i in range(0, min(len(output), len(expected_output))):
            self.assertTrue(isinstance(expected_output[i].content,
                                       six.text_type))
            self.assertTrue(isinstance(output[i].content, six.text_type))
            self.assertEqual(output[i], expected_output[i])


class BaseTestLineBox(BaseTestBox):
    def set_builder(self):
        self._builder = builders.LineBoxBuilder()

    def _test_equal(self, output, expected_output):
        self.assertEqual(len(output), len(expected_output))

        for i in range(0, min(len(output), len(expected_output))):
            self.assertEqual(len(output[i].word_boxes),
                             len(expected_output[i].word_boxes))
            for j in range(0, len(output[i].word_boxes)):
                self.assertEqual(type(output[i].word_boxes[j]),
                                 type(expected_output[i].word_boxes[j]))
            self.assertEqual(output[i], expected_output[i])


class BaseTestDigitLineBox(BaseTestLineBox):
    def set_builder(self):
        self._builder = builders.DigitLineBoxBuilder()
