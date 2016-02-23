#!/usr/bin/env python3
'''
tesseract_capi/ is a wrapper for google's Tesseract-OCR C API
( http://code.google.com/p/tesseract-ocr/ ).

USAGE:
 > from PIL import Image
 > from pyocr.tesseract_api import image_to_string
 > print(image_to_string(Image.open('test.png')))
 > print(image_to_string(Image.open('test-european.jpg'), lang='fra'))

COPYRIGHT:
PyOCR is released under the GPL v3.
Copyright (c) Jerome Flesch, 2011-2012
https://github.com/jflesch/pyocr#readme
'''
import sys

from .. import builders

from . import tesseract_raw
from . import leptonica_raw


__all__ = [
    'can_detect_orientation',
    'detect_orientation',
    'get_available_builders',
    'get_available_languages',
    'get_name',
    'get_version',
    'image_to_string',
    'is_available',
    'TesseractError',
]


class TesseractError(Exception):
    """
    Exception raised when Tesseract fails.
    """
    def __init__(self, status, message):
        Exception.__init__(self, message)
        self.status = status
        self.message = message
        self.args = (status, message)


def can_detect_orientation():
    return True


def detect_orientation(image, lang=None):
    # TODO
    pass


def get_name():
    return "Tesseract (C-API)"


def get_available_builders():
    return [
        builders.TextBuilder,
        builders.WordBoxBuilder,
    ]


def image_to_string(image, lang=None, builder=None):
    if builder is None:
        builder = builders.TextBuilder()
    # TODO
    pass


def is_available():
    # We limit to Python 3. Supporting both Python 2.7 and Python 3.x
    # would be too hard
    python_ver = (sys.version_info[0], sys.version_info[1])
    if python_ver < (3, 0):
        return False
    return tesseract_raw.is_available() and leptonica_raw.is_available()


def get_available_languages():
    # TODO
    return []


def get_version():
    version = tesseract_raw.get_version()
    version = version.split(" ", 1)[0]
    version = version.split(".")
    major = int(version[0])
    minor = int(version[1])
    upd = 0
    if len(version) >= 3:
        upd = int(version[2])
    return (major, minor, upd)
