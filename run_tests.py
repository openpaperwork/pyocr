#!/usr/bin/env python

import sys
sys.path = [ "src" ] + sys.path
import unittest

import pyocr

from tests import tests_tesseract

if __name__ == '__main__':
    print "OCR tool found:"
    for tool in pyocr.get_available_tools():
        print "- %s" % tool.get_name()
    print "---"
    print "Tesseract:"
    unittest.TextTestRunner().run(tests_tesseract.get_all_tests())
