#!/usr/bin/env python2

import sys
import unittest

from tests import tests

if __name__ == '__main__':
    unittest.TextTestRunner().run(tests.get_all_tests())
