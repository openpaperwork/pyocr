#!/usr/bin/env python
"""
Wrapper for various OCR tools.

USAGE:
from PIL import Image
import sys
from pyocr import pyocr

tools = pyocr.get_available_tools()[:]
if len(tools) == 0:
    print("No OCR tool found")
    sys.exit(1)
print("Using '%s'" % (tools[0].get_name()))
tools[0].image_to_string(Image.open('test.png'), lang='fra',
                         builder=TextBuilder())


DETAILS:
Each module wrapping an OCR tool provides the following functions:
- get_name(): Return the name of the tool
- is_available(): Returns True if the tool is installed. False else.
- get_version(): Return a tuple containing the version of the tool (if
  installed)
- get_available_builders(): Returns a list of builders that can be used with
  this tool (see image_to_string())
- get_available_languages(): Returns a list of languages supported by this
  tool. Languages are usually written using ISO 3 letters country codes
- image_to_string():
    Takes 3 arguments:
    - an image (see python Imaging "Image" module) (mandatory)
    - lang=<language> (see get_available_languages()) (optional)
    - builder=<builder> (see get_available_builders() or the classes in the
      module 'pyocr.builders') (optional: default is
      pyocr.builders.TextBuilder)
    Returned value depends of the specified builder.


COPYRIGHT:
Pyocr is released under the GPL v3.
Copyright (c) Jerome Flesch, 2011-2016
Tesseract module: Copyright (c) Samuel Hoffstaetter, 2009

WEBSITE:
https://github.com/jflesch/python-tesseract#readme
"""

from . import cuneiform
from . import libtesseract
from . import tesseract

__all__ = [
    'get_available_tools',
    'TOOLS',
    'VERSION',
]


TOOLS = [  # in preference order
    libtesseract,
    tesseract,
    cuneiform,
]

VERSION = (0, 4, 0)


def get_available_tools():
    """
    Return a list of OCR tools available on the local system.
    """
    available = []
    for tool in TOOLS:
        if tool.is_available():
            available.append(tool)
    return available
