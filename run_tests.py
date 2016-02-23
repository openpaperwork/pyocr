#!/usr/bin/env python

import sys
sys.path = ["src"] + sys.path
import unittest

from pyocr import cuneiform_sh
from pyocr import pyocr
from pyocr import tesseract_capi
from pyocr import tesseract_sh

from tests import tests_cuneiform
from tests import tests_tesseract
from tests import tests_tesseract_capi

if __name__ == '__main__':
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
    if tesseract_capi.is_available():
        print("---")
        print("Tesseract C-API:")
        unittest.TextTestRunner().run(tests_tesseract_capi.get_all_tests())
    if tesseract_sh.is_available():
        print("---")
        print("Tesseract SH:")
        unittest.TextTestRunner().run(tests_tesseract.get_all_tests())
    if cuneiform_sh.is_available():
        print("---")
        print("Cuneiform SH:")
        unittest.TextTestRunner().run(tests_cuneiform.get_all_tests())
