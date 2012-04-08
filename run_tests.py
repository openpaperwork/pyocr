#!/usr/bin/env python2

import sys
sys.path = [ "src" ] + sys.path
import unittest

import pyocr

from tests import tests_cuneiform
from tests import tests_tesseract

if __name__ == '__main__':
    for tool in pyocr.TOOLS:
        print "- OCR: %s" % tool.get_name()
        print "  is_available(): %s" % (str(tool.is_available()))
        print "  get_version(): %s" % (str(tool.get_version()))
        print "  get_available_languages(): ",
        for lang in tool.get_available_languages():
            print ("%s, " % (lang)),
        print ""
    print ""

    print "OCR tool found:"
    for tool in pyocr.get_available_tools():
        print "- %s" % tool.get_name()
    print "---"
    print "Tesseract:"
    unittest.TextTestRunner().run(tests_tesseract.get_all_tests())
    print "---"
    print "Cuneiform:"
    unittest.TextTestRunner().run(tests_cuneiform.get_all_tests())
