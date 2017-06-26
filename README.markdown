# PyOCR

PyOCR is an optical character recognition (OCR) tool wrapper for python.
That is, it helps using OCR tools from a Python program.

It has been tested only on GNU/Linux systems. It should also work on similar
systems (*BSD, etc). It may or may not work on Windows, MacOSX, etc.

PyOCR can be used as a wrapper for google's
[Tesseract-OCR](http://code.google.com/p/tesseract-ocr/) or Cuneiform.
It can read all image types supported by
[Pillow](https://github.com/python-imaging/Pillow), including jpeg, png, gif,
bmp, tiff, and others. It also support bounding box data.


## Supported OCR tools

* Libtesseract (C API)
* Tesseract (fork + exec)
* Cuneiform (fork + exec)


## Features

* Support all the image formats supported by [Pillow](https://github.com/python-imaging/Pillow)
* As output, can provide a simple string or boxes (position + string for each word and line)
* Can focus on digits only (Tesseract only)
* Can save and reload boxes in hOCR format


## Limitations

* hOCR: Only a subset of the specification is supported. For instance, pages and paragraph positions are not stored.


## Installation

```sh
sudo pip install pyocr  # Python 2.7
sudo pip3 install pyocr  # Python 3.X
```

or the manual way:
```sh
mkdir -p ~/git ; cd git
git clone https://github.com/jflesch/pyocr.git
cd pyocr
sudo python ./setup.py install
```


## Usage

### Initialization

```Python
from PIL import Image
import sys

import pyocr
import pyocr.builders

tools = pyocr.get_available_tools()
if len(tools) == 0:
    print("No OCR tool found")
    sys.exit(1)
# The tools are returned in the recommended order of usage
tool = tools[0]
print("Will use tool '%s'" % (tool.get_name()))
# Ex: Will use tool 'libtesseract'

langs = tool.get_available_languages()
print("Available languages: %s" % ", ".join(langs))
lang = langs[0]
print("Will use lang '%s'" % (lang))
# Ex: Will use lang 'fra'
# Note that languages are NOT sorted in any way. Please refer
# to the system locale settings for the default language
# to use.
```

### Image to text

```Python
txt = tool.image_to_string(
    Image.open('test.png'),
    lang=lang,
    builder=pyocr.builders.TextBuilder()
)
# txt is a Python string

word_boxes = tool.image_to_string(
    Image.open('test.png'),
    lang="eng",
    builder=pyocr.builders.WordBoxBuilder()
)
# list of box objects. For each box object:
#   box.content is the word in the box
#   box.position is its position on the page (in pixels)
#
# Beware that some OCR tools (Tesseract for instance)
# may return empty boxes

line_and_word_boxes = tool.image_to_string(
    Image.open('test.png'), lang="fra",
    builder=pyocr.builders.LineBoxBuilder()
)
# list of line objects. For each line object:
#   line.word_boxes is a list of word boxes (the individual words in the line)
#   line.content is the whole text of the line
#   line.position is the position of the whole line on the page (in pixels)
#
# Beware that some OCR tools (Tesseract for instance)
# may return empty boxes

# Digits - Only Tesseract (not 'libtesseract' yet !)
digits = tool.image_to_string(
    Image.open('test-digits.png'),
    lang=lang,
    builder=pyocr.tesseract.DigitBuilder()
)
# digits is a python string
```

Argument 'lang' is optional. The default value depends of
the tool used.

Argument 'builder' is optional. Default value is
builders.TextBuilder().

If the OCR fails, an exception ```pyocr.PyocrException```
will be raised.

An exception MAY be raised if the input image contains no
text at all (depends on the OCR tool behavior).


### Orientation detection

Currently only available with Tesseract or Libtesseract.

```Python
if tool.can_detect_orientation():
    try:
        orientation = tool.detect_orientation(
            Image.open('test.png'),
            lang='fra'
        )
    except pyocr.PyocrException as exc:
        print("Orientation detection failed: {}".format(exc))
        return
    print("Orientation: {}".format(orientation))
# Ex: Orientation: {
#   'angle': 90,
#   'confidence': 123.4,
# }
```

Angles are given in degrees (range: [0-360[). Exact possible
values depend of the tool used. Tesseract only returns angles =
0, 90, 180, 270.

Confidence is a score arbitrarily defined by the tool. It MAY not
be returned.

detect_orientation() MAY raise an exception if there is no text
detected in the image.


### Writing and reading text files

Writing:

```Python
import codecs
import pyocr
import pyocr.builders

tool = pyocr.get_available_tools()[0]
builder = pyocr.builders.TextBuilder()

txt = tool.image_to_string(
    Image.open('test.png'),
    lang=lang,
    builder=builder
)
# txt is a Python string

with codecs.open("toto.txt", 'w', encoding='utf-8') as file_descriptor:
    builder.write_file(file_descriptor, txt)
# toto.txt is a simple text file, encoded in utf-8
```

Reading:

```Python
import codecs
import pyocr.builders

builder = pyocr.builders.TextBuilder()
with codecs.open("toto.txt", 'r', encoding='utf-8') as file_descriptor:
    txt = builder.read_file(file_descriptor)
# txt is a Python string
```

### Writing and reading hOCR files

Writing:

```Python
import codecs
import pyocr
import pyocr.builders

tool = pyocr.get_available_tools()[0]
builder = pyocr.builders.LineBoxBuilder()

line_boxes = tool.image_to_string(
    Image.open('test.png'),
    lang=lang,
    builder=builder
)
# list of LineBox (each box points to a list of word boxes)

with codecs.open("toto.html", 'w', encoding='utf-8') as file_descriptor:
    builder.write_file(file_descriptor, line_boxes)
# toto.html is a valid XHTML file
```

Reading:

```Python
import codecs
import pyocr.builders

builder = pyocr.builders.LineBoxBuilder()
with codecs.open("toto.html", 'r', encoding='utf-8') as file_descriptor:
    line_boxes = builder.read_file(file_descriptor)
# list of LineBox (each box points to a list of word boxes)
```


## Dependencies

* PyOCR requires python 2.7 or later. Python 3 is supported.
* You will need [Pillow](https://github.com/python-imaging/Pillow)
  or Python Imaging Library (PIL). Under Debian/Ubuntu, Pillow is in
  the package ```python-pil``` (```python3-pil``` for the Python 3
  version).
* Install an OCR:
  * [libtesseract](http://code.google.com/p/tesseract-ocr/)
    ('libtesseract3' + 'tesseract-ocr-&lt;lang&gt;' in Debian).
  * or [tesseract-ocr](http://code.google.com/p/tesseract-ocr/)
    ('tesseract-ocr' + 'tesseract-ocr-&lt;lang&gt;' in Debian).
    You must be able to invoke the tesseract command as "tesseract".
    PyOCR is tested with Tesseract >= 3.01 only.
  * or Cuneiform


## Tests

```sh
python ./run_tests.py
```

Tests are made to be run with the latest versions of Tesseract and Cuneiform.
the first tests verify that you're using the expected version.

To run the tesseract tests, you will need the following lang data files:
- English (tesseract-ocr-eng)
- French (tesseract-ocr-fra)
- Japanese (tesseract-ocr-jpn)


## OCR on natural scenes

If you want to run OCR on natural scenes (photos, etc), you will have to filter
the image first. There are many algorithms possible to do that. One of those
who gives the best results is
[Stroke Width Transform](https://github.com/jflesch/libpillowfight#stroke-width-transformation).


## Contact

* [Mailing-list](https://github.com/jflesch/paperwork/wiki/Contact#mailing-list)
* [Bug tracker](https://github.com/jflesch/pyocr/issues/)


## Applications that use PyOCR

* [Mayan EDMS](http://mayan-edms.com/)
* [Paperless](https://github.com/danielquinn/paperless#readme)
* [Paperwork](https://github.com/jflesch/paperwork#readme)

If you know of any other applications that use Pyocr, please
[tell us](https://github.com/jflesch/paperwork/wiki/Contact#mailing-list) :-)

## Copyright

PyOCR is released under the GPL v3+.
Copyright belongs to the authors of each piece of code
(see the file AUTHORS for the contributors list, and
```git blame``` to know which lines belong to which author).

https://github.com/jflesch/pyocr
