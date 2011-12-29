#!/usr/bin/env python
'''
Python-tesseract is a wrapper for google's Tesseract-OCR
( http://code.google.com/p/tesseract-ocr/ ).

USAGE:
 > import Image
 > from tesseract import image_to_string
 > print image_to_string(Image.open('test.png'))
 > print image_to_string(Image.open('test-european.jpg'), lang='fra')

COPYRIGHT:
Python-tesseract is released under the GPL v3.
Copyright (c) Samuel Hoffstaetter, 2009
Copyright (c) Jerome Flesch, 2011
http://wiki.github.com/jflesch/python-tesseract
'''

import codecs
import os
import StringIO
import subprocess
import sys

# CHANGE THIS IF TESSERACT IS NOT IN YOUR PATH, OR IS NAMED DIFFERENTLY
TESSERACT_CMD = 'tesseract'

TESSDATA_POSSIBLE_PATHS = [
    "/usr/local/share/tessdata",
    "/usr/share/tessdata",
]

TESSDATA_EXTENSION = ".traineddata"

__all__ = [
    'get_available_languages',
    'image_to_string',
    'is_tesseract_available',
    'read_box_file',
    'TesseractBox',
    'write_box_file',
    'get_tesseract_version',
]


def run_tesseract(input_filename, output_filename_base, lang=None,
                  boxes=False):
    '''
    runs the command:
        `TESSERACT_CMD` `input_filename` `output_filename_base`

    returns the exit status of tesseract, as well as tesseract's stderr output

    '''

    command = [TESSERACT_CMD, input_filename, output_filename_base]

    if lang is not None:
        command += ['-l', lang]

    if boxes:
        command += ['batch.nochop', 'makebox']

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
    ''' tries to remove the given filename. Ignores non-existent files '''
    try:
        os.remove(filename)
    except OSError:
        pass


def get_errors(error_string):
    '''
    returns all lines in the error_string that start with the string "error"

    '''

    lines = error_string.splitlines()
    error_lines = tuple(line for line in lines if line.find('Error') >= 0)
    if len(error_lines) > 0:
        return '\n'.join(error_lines)
    else:
        return error_string.strip()


def tempnam():
    ''' returns a temporary file-name '''

    # prevent os.tmpname from printing an error...
    stderr = sys.stderr
    try:
        sys.stderr = StringIO.StringIO()
        return os.tempnam(None, 'tess_')
    finally:
        sys.stderr = stderr


class TesseractError(Exception):
    """
    Exception raised when Tesseract fails.
    """
    def __init__(self, status, message):
        Exception.__init__(self, message)
        self.status = status
        self.message = message
        self.args = (status, message)


class TesseractBox(object):
    """
    Tesseract Box: Tesseract boxes are rectangles around each individual
    character recognized in the image.
    """
    def __init__(self, char, position, page):
        """
        Instantiate a Tesseract box

        Arguments:
            char --- character found in this box
            position --- the position of the box on the image. Given as a
                tuple of tuple:
                ((width_pt_x, height_pt_x), (width_pt_y, height_pt_y))
            page --- page number, as specified in the box file (usually 0)
        """
        self.char = char
        self.position = position
        self.page = page

    def get_unicode_string(self):
        """
        Return the string corresponding to the box, in unicode (utf8).
        This string can be stored in a file as-is (see write_box_file())
        and reread using read_box_file().
        """
        return "%s %d %d %d %d %d" % (
            self.char,
            self.position[0][0],
            self.position[0][1],
            self.position[1][0],
            self.position[1][1],
            self.page
        )

    def __str__(self):
        return self.get_unicode_string().encode('ascii', 'replace')

    def __box_cmp(self, other):
        """
        Comparison function.
        """
        if other == None:
            return -1
        for cmp_result in (cmp(self.page, other.page),
                           cmp(self.char, other.char),
                           cmp(self.position[0][1], other.position[0][1]),
                           cmp(self.position[1][1], other.position[1][1]),
                           cmp(self.position[0][0], other.position[0][0]),
                           cmp(self.position[1][0], other.position[1][0])):
            if cmp_result != 0:
                return cmp_result
        return 0

    def __lt__(self, other):
        return self.__box_cmp(other) < 0

    def __gt__(self, other):
        return self.__box_cmp(other) > 0

    def __eq__(self, other):
        return self.__box_cmp(other) == 0

    def __le__(self, other):
        return self.__box_cmp(other) <= 0

    def __ge__(self, other):
        return self.__box_cmp(other) >= 0

    def __ne__(self, other):
        return self.__box_cmp(other) != 0

    def __hash__(self):
        position_hash = 0
        position_hash += ((self.position[0][0] & 0xFF) << 0)
        position_hash += ((self.position[0][1] & 0xFF) << 8)
        position_hash += ((self.position[1][0] & 0xFF) << 16)
        position_hash += ((self.position[1][1] & 0xFF) << 24)
        return (position_hash ^ hash(self.char) ^ hash(self.page))


def read_box_file(file_descriptor):
    """
    Extract of set of TesseractBox from the lines of 'file_descriptor'

    Return:
        An array of TesseractBox.
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
        box = TesseractBox(elements[0], position, int(elements[5]))
        boxes.append(box)
    return boxes


def write_box_file(file_descriptor, boxes):
    """
    Write boxes in a box file. Output is in a the same format than tesseract's
    one.

    Warning:
        The file_descriptor must support UTF-8 ! (see module 'codecs')
    """
    for box in boxes:
        file_descriptor.write(box.get_unicode_string() + "\n")


def image_to_string(image, lang=None, boxes=False):
    '''
    Runs tesseract on the specified image. First, the image is written to disk,
    and then the tesseract command is run on the image. Tesseract's result is
    read, and the temporary files are erased.

    Returns:
        if boxes == False (default): the text as read from the image
        if boxes == True: an array of TesseractBox

    Warning:
        the returned string is encoded in UTF-8
    '''

    input_file_name = '%s.bmp' % tempnam()
    output_file_name_base = tempnam()
    if not boxes:
        output_file_name = '%s.txt' % output_file_name_base
    else:
        output_file_name = '%s.box' % output_file_name_base
    try:
        image.save(input_file_name)
        (status, errors) = run_tesseract(input_file_name,
                                         output_file_name_base,
                                         lang=lang,
                                         boxes=boxes)
        if status:
            raise TesseractError(status, errors)
        file_desc = codecs.open(output_file_name, 'r', encoding='utf-8')
        try:
            if not boxes:
                return file_desc.read().strip()
            else:
                return read_box_file(file_desc)
        finally:
            file_desc.close()
    finally:
        cleanup(input_file_name)
        cleanup(output_file_name)


def is_tesseract_available():
    """
    Indicates if tesseract appears to be installed.

    Returns:
        True --- if it is installed
        False --- if it isn't
    """
    for dirpath in os.environ["PATH"].split(os.pathsep):
        path = os.path.join(dirpath, TESSERACT_CMD)
        if os.path.exists(path) and os.access(path, os.X_OK):
            return True
    return False


def get_available_languages():
    """
    Returns the list of languages that Tesseract knows how to handle

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
    Return Tesseract version.

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
    ret = proc.wait()
    if not ret in (0, 1):
        raise TesseractError(ret, ver_string)

    try:
        major = int(ver_string.split(" ")[1].split(".")[0])
        minor = int(ver_string.split(" ")[1].split(".")[1])
    except IndexError:
        raise TesseractError(ret,
                ("Unable to parse Tesseract version (spliting failed): [%s]"
                 % (ver_string)))
    except ValueError:
        raise TesseractError(ret,
                ("Unable to parse Tesseract version (not a number): [%s]"
                 % (ver_string)))

    # minor must also be splited
    update = (minor % 10)
    minor /= 10

    return (major, minor, update)
