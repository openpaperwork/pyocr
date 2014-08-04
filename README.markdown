# PyOCR

Pyocr is an optical character recognition (OCR) tool wrapper for python.
That is, it helps using OCR tools from a Python program.

It has been tested only on GNU/Linux systems. It should also work on similar
systems (*BSD, etc). It doesn't work on Windows, MacOSX, etc.

Pyocr can be used as a wrapper for google's
[Tesseract-OCR](http://code.google.com/p/tesseract-ocr/) or Cuneiform.
It can read all image types supported by
[Pillow](https://github.com/python-imaging/Pillow), including jpeg, png, gif,
bmp, tiff, and others. It also support bounding box data.


## Usage

    from PIL import Image
    import sys

    import pyocr
    import pyocr.builders

    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        print("No OCR tool found")
        sys.exit(1)
    tool = tools[0]
    print("Will use tool '%s'" % (tool.get_name()))
    # Ex: Will use tool 'tesseract'

    langs = tool.get_available_languages()
    print("Available languages: %s" % ", ".join(langs))
    lang = langs[0]
    print("Will use lang '%s'" % (lang))
    # Ex: Will use lang 'fra'

    txt = tool.image_to_string(Image.open('test.png'),
                               lang=lang,
                               builder=pyocr.builders.TextBuilder())
    word_boxes = tool.image_to_string(Image.open('test.png'),
                                      lang=lang,
                                      builder=pyocr.builders.WordBoxBuilder())
    line_and_word_boxes = tool.image_to_string(
            Image.open('test.png'), lang=lang,
            builder=pyocr.builders.LineBoxBuilder())
            
    # Digits - Only Tesseract
    digits = tool.image_to_string(Image.open('test-digits.png'),
                                  lang=lang,
                                  builder=pyocr.tesseract.DigitBuilder())    


## Dependencies

* Pyocr requires python 2.6 or later.
* You will need [Pillow](https://github.com/python-imaging/Pillow)
  or Python Imaging Library (PIL). Under Debian/Ubuntu, PIL is in
  the package "python-imaging".
* Install an OCR:
  * tesseract-ocr from http://code.google.com/p/tesseract-ocr/
    ('tesseract-ocr' + 'tesseract-ocr-&lt;lang&gt;' in Debian).
    You must be able to invoke the tesseract command as "tesseract".
    Python-tesseract is tested with Tesseract >= 3.01 only.
  * or cuneiform


## Installation

    $ sudo python ./setup.py install


## Tests

    $ python ./run_tests.py

Tests are made to be run with the latest versions of Tesseract and Cuneiform.
the first tests verify that you're using the expected version.

To run the tests, you will need the following lang support:
- English (tesseract-ocr-eng)
- French (tesseract-ocr-fra)
- Japanese (tesseract-ocr-jpn)


## Copyright

Pyocr is released under the GPL v3+.

tesseract.py:

* Copyright (c) Samuel Hoffstaetter, 2009
* Copyright (c) Jerome Flesch, 2011-2013

other files:

* Copyright (c) Jerome Flesch, 2011-2013

https://github.com/jflesch/pyocr
