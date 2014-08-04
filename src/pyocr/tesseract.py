#!/usr/bin/env python
'''
tesseract.py is a wrapper for google's Tesseract-OCR
( http://code.google.com/p/tesseract-ocr/ ).

USAGE:
 > from PIL import Image
 > from tesseract import image_to_string
 > print(image_to_string(Image.open('test.png')))
 > print(image_to_string(Image.open('test-european.jpg'), lang='fra'))

COPYRIGHT:
Pyocr is released under the GPL v3.
Copyright (c) Samuel Hoffstaetter, 2009
Copyright (c) Jerome Flesch, 2011-2012
https://github.com/jflesch/python-tesseract#readme
'''

import codecs
import os
import subprocess
import sys
import tempfile
import xml.dom.minidom

from . import builders
from . import util


# CHANGE THIS IF TESSERACT IS NOT IN YOUR PATH, OR IS NAMED DIFFERENTLY
TESSERACT_CMD = 'tesseract'

TESSDATA_POSSIBLE_PATHS = [
    "/usr/local/share/tessdata",
    "/usr/share/tessdata",
    "/usr/share/tesseract/tessdata",
    "/usr/local/share/tesseract-ocr/tessdata",
    "/usr/share/tesseract-ocr/tessdata",
    "/app/vendor/tesseract-ocr/tessdata",  # Heroku
]

TESSDATA_EXTENSION = ".traineddata"


__all__ = [
    'CharBoxBuilder',
    'DigitBuilder'
    'get_available_builders',
    'get_available_languages',
    'get_name',
    'get_version',
    'image_to_string',
    'is_available',
    'TesseractError',
]


class CharBoxBuilder(object):
    """
    If passed to image_to_string(), image_to_string() will return an array of
    Box. Each box correspond to a character recognized in the image.
    """

    file_extensions = ["box"]
    tesseract_configs = ['batch.nochop', 'makebox']

    def __init__(self):
        pass

    @staticmethod
    def read_file(file_descriptor):
        """
        Extract of set of Box from the lines of 'file_descriptor'

        Return:
            An array of Box.
        """
        boxes = []  # note that the order of the boxes may matter to the caller
        for line in file_descriptor.readlines():
            line = line.strip()
            if line == "":
                continue
            elements = line.split(" ")
            if len(elements) < 6:
                continue
            position = ((int(elements[1]), int(elements[2])),
                        (int(elements[3]), int(elements[4])))
            box = builders.Box(elements[0], position)
            boxes.append(box)
        return boxes

    @staticmethod
    def write_file(file_descriptor, boxes):
        """
        Write boxes in a box file. Output is in a the same format than
        tesseract's one.

        Warning:
            The file_descriptor must support UTF-8 ! (see module 'codecs')
        """
        for box in boxes:
            file_descriptor.write(box.get_unicode_string() + " 0\n")

    @staticmethod
    def __str__():
        return "Character boxes"


class DigitBuilder(builders.TextBuilder):
    """
    If passed to image_to_string(), image_to_string() will return a string with only digits.
    Characters recognition will consider text as if it will only composed by digits
    """

    @staticmethod
    def __str__():
        return "Digits only"

    def __init__(self, tesseract_layout=3):
        super(DigitBuilder, self).__init__(tesseract_layout)
        self.tesseract_configs.append("digits")


def get_name():
    return "Tesseract"


def get_available_builders():
    return [
        builders.TextBuilder,
        builders.WordBoxBuilder,
        CharBoxBuilder,
    ]


def run_tesseract(input_filename, output_filename_base, lang=None,
                  configs=None):
    '''
    Runs Tesseract:
        `TESSERACT_CMD` \
                `input_filename` \
                `output_filename_base` \
                [-l `lang`] \
                [`configs`]

    Arguments:
        input_filename --- image to read
        output_filename_base --- file name in which must be stored the result
            (without the extension)
        lang --- Tesseract language to use (if None, none will be specified)
        config --- List of Tesseract configs to use (if None, none will be
            specified)

    Returns:
        Returns (the exit status of Tesseract, Tesseract's output)
    '''

    command = [TESSERACT_CMD, input_filename, output_filename_base]

    if lang is not None:
        command += ['-l', lang]

    if configs != None:
        command += configs

    proc = subprocess.Popen(command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    # Beware that in some cases, tesseract may print more on stderr than
    # allowed by the buffer of subprocess.Popen.stderr. So we must read stderr
    # asap or Tesseract will remain stuck when trying to write again on stderr.
    # In the end, we just have to make sure that proc.stderr.read() is called
    # before proc.wait()
    errors = proc.stdout.read()
    return (proc.wait(), errors)


def cleanup(filename):
    ''' Tries to remove the given filename. Ignores non-existent files '''
    try:
        os.remove(filename)
    except OSError:
        pass


def temp_file(suffix):
    ''' Returns a temporary file '''
    return tempfile.NamedTemporaryFile(prefix='tess_', suffix=suffix)


class TesseractError(Exception):
    """
    Exception raised when Tesseract fails.
    """
    def __init__(self, status, message):
        Exception.__init__(self, message)
        self.status = status
        self.message = message
        self.args = (status, message)


def image_to_string(image, lang=None, builder=None):
    '''
    Runs tesseract on the specified image. First, the image is written to disk,
    and then the tesseract command is run on the image. Tesseract's result is
    read, and the temporary files are erased.

    Arguments:
        image --- image to OCR
        lang --- tesseract language to use
        builder --- builder used to configure Tesseract and read its result.
            The builder is used to specify the type of output expected.
            Possible builders are TextBuilder or CharBoxBuilder. If builder ==
            None, the builder used will be TextBuilder.

    Returns:
        Depends of the specified builder. By default, it will return a simple
        string.
    '''

    if builder == None:
        builder = builders.TextBuilder()

    with temp_file(".bmp") as input_file:
        with temp_file('')  as output_file:
            output_file_name_base = output_file.name

        image = image.convert("RGB")
        image.save(input_file.name)
        (status, errors) = run_tesseract(input_file.name,
                                         output_file_name_base,
                                         lang=lang,
                                         configs=builder.tesseract_configs)
        if status:
            raise TesseractError(status, errors)

        output_file_name = "ERROR"
        for file_extension in builder.file_extensions:
            output_file_name = ('%s.%s' % (output_file_name_base,
                                           file_extension))
            if not os.access(output_file_name, os.F_OK):
                continue

            try:
                with codecs.open(output_file_name, 'r', encoding='utf-8',
                                 errors='replace') as file_desc:
                    results = builder.read_file(file_desc)
                return results
            finally:
                cleanup(output_file_name)
            break
        raise TesseractError(-1, "Unable to find output file"
                             " last name tried: %s" % output_file_name)


def is_available():
    return util.is_on_path(TESSERACT_CMD)


def get_available_languages():
    """
    Returns the list of languages that Tesseract knows how to handle.

    Returns:
        An array of strings. Note that most languages name conform to ISO 639
        terminology, but not all. Most of the time, truncating the language
        name name returned by this function to 3 letters should do the trick.
    """
    langs = []
    for dirpath in TESSDATA_POSSIBLE_PATHS:
        if not os.access(dirpath, os.R_OK):
            continue
        for filename in os.listdir(dirpath):
            if filename.lower().endswith(TESSDATA_EXTENSION):
                lang = filename[:(-1 * len(TESSDATA_EXTENSION))]
                langs.append(lang)
    return langs


def get_version():
    """
    Returns Tesseract version.

    Returns:
        A tuple corresponding to the version (for instance, (3, 0, 1) for 3.01)

    Exception:
        TesseractError --- Unable to run tesseract or to parse the version
    """
    command = [TESSERACT_CMD, "-v"]

    proc = subprocess.Popen(command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    ver_string = proc.stdout.read()
    if hasattr(ver_string, 'decode'):
        ver_string = ver_string.decode('utf-8')
    ret = proc.wait()
    if not ret in (0, 1):
        raise TesseractError(ret, ver_string)

    try:
        els = ver_string.split(" ")[1].split(".")
        els = [int(x) for x in els]
        major = els[0]
        minor = els[1]
        upd = 0
        if len(els) >= 3:
            upd = els[2]
        return (major, minor, upd)
    except IndexError:
        raise TesseractError(ret,
                ("Unable to parse Tesseract version (spliting failed): [%s]"
                 % (ver_string)))
    except ValueError:
        raise TesseractError(ret,
                ("Unable to parse Tesseract version (not a number): [%s]"
                 % (ver_string)))

