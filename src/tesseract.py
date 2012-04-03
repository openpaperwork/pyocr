#!/usr/bin/env python2
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
https://github.com/jflesch/python-tesseract#readme
'''

import codecs
import os
import StringIO
import subprocess
import sys
import xml.dom.minidom


# CHANGE THIS IF TESSERACT IS NOT IN YOUR PATH, OR IS NAMED DIFFERENTLY
TESSERACT_CMD = 'tesseract'

TESSDATA_POSSIBLE_PATHS = [
    "/usr/local/share/tessdata",
    "/usr/share/tessdata",
]

TESSDATA_EXTENSION = ".traineddata"


__all__ = [
    'Box',
    'CharBoxBuilder',
    'get_available_languages',
    'get_version',
    'image_to_string',
    'is_tesseract_available',
    'read_box_file',
    'TesseractError',
    'TextBuilder',
    'WordBoxBuilder',
    'write_box_file',
]


class TextBuilder(object):
    """
    If passed to image_to_string(), image_to_string() will return a simple
    string. This string will be the output of Tesseract, as-is.

    Warning:
        The returned string is encoded in UTF-8
    """

    file_extension = "txt"
    tesseract_configs = []

    def __init__(self):
        pass

    @staticmethod
    def read_file(file_descriptor):
        """
        Read a file and extract the content as a string
        """
        return file_descriptor.read().strip()

    @staticmethod
    def write_file(file_descriptor, text):
        """
        Write a string in a file
        """
        file_descriptor.write(text)


class Box(object):
    """
    Tesseract Box: Tesseract boxes are rectangles around each individual
    element recognized in the image. Elements are char or word depending
    of the builder.
    """

    def __init__(self, content, position):
        """
        Instantiate a Tesseract box

        Arguments:
            content --- a single string
            position --- the position of the box on the image. Given as a
                tuple of tuple:
                ((width_pt_x, height_pt_x), (width_pt_y, height_pt_y))
        """
        self.content = content
        self.position = position

    def get_unicode_string(self):
        """
        Return the string corresponding to the box, in unicode (utf8).
        This string can be stored in a file as-is (see write_box_file())
        and reread using read_box_file().
        """
        return "%s %d %d %d %d" % (
            self.content,
            self.position[0][0],
            self.position[0][1],
            self.position[1][0],
            self.position[1][1],
        )

    def get_xml_tag(self):
        span_tag = xml.dom.minidom.Element("span")
        span_tag.setAttribute("class", "ocr_word")
        span_tag.setAttribute("title", ("bbox %d %d %d %d" % (
                (self.position[0][0], self.position[0][1],
                 self.position[1][0], self.position[1][1]))))
        txt = xml.dom.minidom.Text()
        txt.data = self.content
        span_tag.appendChild(txt)
        return span_tag

    def __str__(self):
        return self.get_unicode_string().encode('ascii', 'replace')

    def __box_cmp(self, other):
        """
        Comparison function.
        """
        if other == None:
            return -1
        for cmp_result in (cmp(self.position[0][1], other.position[0][1]),
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
        return (position_hash ^ hash(self.content) ^ hash(self.content))


class CharBoxBuilder(object):
    """
    If passed to image_to_string(), image_to_string() will return an array of
    Box. Each box correspond to a character recognized in the image.
    """

    file_extension = "box"
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
            box = Box(elements[0], position)
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


class WordBoxBuilder(object):
    """
    If passed to image_to_string(), image_to_string() will return an array of
    Box. Each box correspond to a word recognized in the image.
    """

    file_extension = "html"
    tesseract_configs = ['hocr']

    def __init__(self):
        pass

    @staticmethod
    def __parse_position(xml_tag):
        title = xml_tag.getAttribute("title")
        title = title.split("; ")
        title = title[-1]
        title = title.split(" ")
        position = ((int(title[1]), int(title[2])),
                    (int(title[3]), int(title[4])))
        return position

    @staticmethod
    def __extract_txt(xml_tag):
        txt = u""
        for tag in xml_tag.childNodes:
            if tag.nodeType == tag.TEXT_NODE:
                txt += tag.wholeText
            else:
                txt += WordBoxBuilder.__extract_txt(tag)
        return txt

        element = elements[0]

    @staticmethod
    def read_file(file_descriptor):
        """
        Extract of set of Box from the lines of 'file_descriptor'

        Return:
            An array of Box.
        """
        xml_string = file_descriptor.read().encode("utf-8")
        xml_doc = xml.dom.minidom.parseString(xml_string)
        boxes = []
        for tag in xml_doc.getElementsByTagName("span"):
            if ("ocr_word" != tag.getAttribute("class")):
                continue
            txt = WordBoxBuilder.__extract_txt(tag)
            position = WordBoxBuilder.__parse_position(tag)
            box = Box(txt, position)
            boxes.append(box)
        return boxes

    @staticmethod
    def write_file(file_descriptor, boxes):
        """
        Write boxes in a box file. Output is a *very* *simplified* version
        of hOCR.

        Warning:
            The file_descriptor must support UTF-8 ! (see module 'codecs')
        """
        file_descriptor.write(u"<body>\n")
        for box in boxes:
            file_descriptor.write(box.get_xml_tag().toxml() + u"\n")
        file_descriptor.write(u"</body>\n")


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


def tempnam():
    ''' Returns a temporary file-name '''

    # prevent os.tempnam from printing an error...
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
        builder = TextBuilder()

    input_file_name = '%s.bmp' % tempnam()
    output_file_name_base = tempnam()
    output_file_name = ('%s.%s' % (output_file_name_base,
                                   builder.file_extension))

    try:
        image.save(input_file_name)
        (status, errors) = run_tesseract(input_file_name,
                                         output_file_name_base,
                                         lang=lang,
                                         configs=builder.tesseract_configs)
        if status:
            raise TesseractError(status, errors)
        with codecs.open(output_file_name, 'r', encoding='utf-8') as file_desc:
            results = builder.read_file(file_desc)
        return results
    finally:
        cleanup(input_file_name)
        cleanup(output_file_name)


def is_tesseract_available():
    """
    Indicates if Tesseract appears to be installed.

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
