#!/usr/bin/env python3

import sys
sys.path = ["src"] + sys.path
import unittest

from pyocr import cuneiform
from pyocr import pyocr
from pyocr import libtesseract
from pyocr import tesseract

from tests import tests_cuneiform
from tests import tests_tesseract
from tests import tests_libtesseract

if __name__ == '__main__':
    success = True

    for tool in pyocr.TOOLS:
        print("- OCR: %s" % tool.get_name())
        available = tool.is_available()
        print("  is_available(): %s" % (str(available)))
        if available:
            print("  get_version(): %s" % (str(tool.get_version())))
            print("  get_available_languages(): ")
            print("    " + ", ".join(tool.get_available_languages()))
        print("")
    print("")

    print("OCR tool found:")
    for tool in pyocr.get_available_tools():
        print("- %s" % tool.get_name())
    if libtesseract.is_available():
        print("---")
        print("Tesseract C-API:")
        success = unittest.TextTestRunner().run(
            tests_libtesseract.get_all_tests()
        ).wasSuccessful() and success
    if tesseract.is_available():
        print("---")
        print("Tesseract SH:")
        success = unittest.TextTestRunner().run(
            tests_tesseract.get_all_tests()
        ).wasSuccessful() and success
    if cuneiform.is_available():
        print("---")
        print("Cuneiform SH:")
        success = unittest.TextTestRunner().run(
            tests_cuneiform.get_all_tests()
        ).wasSuccessful() and success

    sys.exit(0 if success else 1)
