Pyocr is an optical character recognition (OCR) tool wrapper for python.
That is, it helps using OCR tools from a Python program.

It has been tested only on GNU/Linux systems. It should also work on similar
systems (*BSD, etc). It doesn't work on Windows, MacOSX, etc.

Pyocr can be used as a wrapper for google's
[Tesseract-OCR](http://code.google.com/p/tesseract-ocr/) or Cuneiform.
It can read all image types supported by
[Pillow](https://github.com/python-imaging/Pillow), including jpeg, png, gif,
bmp, tiff, and others. It also support bounding box data.


# Usage

    from PIL import Image
    import sys

    from pyocr import pyocr
	import pyocr.builders

    tools = pyocr.get_available_tools()[:]
    if len(tools) == 0:
        print("No OCR tool found")
        sys.exit(1)
    print("Using '%s'" % (tools[0].get_name()))
    txt = tools[0].image_to_string(Image.open('test.png'),
	                               lang='fra',
                                   builder=pyocr.builders.TextBuilder())


# Dependencies

* Pyocr requires python 2.7 or later.
* You will need [Pillow](https://github.com/python-imaging/Pillow)
  or Python Imaging Library (PIL). Under Debian/Ubuntu, PIL is in
  the package "python-imaging".
* Install an OCR:
  * tesseract-ocr from http://code.google.com/p/tesseract-ocr/
    ('tesseract-ocr' + 'tesseract-ocr-&lt;lang&gt;' in Debian).
    You must be able to invoke the tesseract command as "tesseract".
    Python-tesseract is tested with Tesseract >= 3.01 only.
  * or cuneiform


# Installation

    $ sudo python ./setup.py install


# Tests

Tests are made to be run with the latest versions of Tesseract and Cuneiform.
the first tests verifie that you're using the expected version.


# Copyright

Pyocr is released under the GPL v3+.
tesseract.py:
  Copyright (c) Samuel Hoffstaetter, 2009
  Copyright (c) Jerome Flesch, 2011-2013
other files:
  Copyright (c) Jerome Flesch, 2011-2013

https://github.com/jflesch/pyocr
