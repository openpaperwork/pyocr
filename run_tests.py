#!/usr/bin/env python

import sys
import unittest

from tests import tests

if __name__ == '__main__':
    all_tests = unittest.TestSuite()
    all_tests.addTest(tests.get_txt_testsuite())
    unittest.TextTestRunner().run(all_tests)
