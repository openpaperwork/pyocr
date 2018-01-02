#!/usr/bin/env python
'''
tesseract.py is a wrapper for google's Tesseract-OCR
( http://code.google.com/p/tesseract-ocr/ ).

USAGE:
 > from PIL import Image
 > from pyocr.tesseract import image_to_string
 > print(image_to_string(Image.open('test.png')))
 > print(image_to_string(Image.open('test-european.jpg'), lang='fra'))

COPYRIGHT:
PyOCR is released under the GPL v3.
Copyright (c) Samuel Hoffstaetter, 2009
Copyright (c) Jerome Flesch, 2011-2016
https://github.com/openpaperwork/pyocr#readme
'''

import codecs
import logging
import os
import subprocess
import sys
import tempfile
import contextlib
import shutil

from . import builders
from . import util
from .builders import DigitBuilder  # backward compatibility
from .error import TesseractError  # backward compatibility
from .util import digits_only

# CHANGE THIS IF TESSERACT IS NOT IN YOUR PATH, OR IS NAMED DIFFERENTLY
TESSERACT_CMD = 'tesseract.exe' if os.name == 'nt' else 'tesseract'

TESSDATA_EXTENSION = ".traineddata"

logger = logging.getLogger(__name__)

g_subprocess_startup_info = None
g_creation_flags = 0

__all__ = [
    'CharBoxBuilder',
    'DigitBuilder',
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


class CharBoxBuilder(builders.BaseBuilder):
    """
    If passed to image_to_string(), image_to_string() will return an array of
    Box. Each box correspond to a character recognized in the image.
    """

    def __init__(self):
        file_ext = ["box"]
        tess_flags = []
        tess_conf = ["batch.nochop", "makebox"]
        cun_args = []
        super(CharBoxBuilder, self).__init__(file_ext, tess_flags, tess_conf,
                                             cun_args)
        self.tesseract_layout = 1

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


def _set_environment():
    global g_subprocess_startup_info
    global g_creation_flags

    if os.name == "nt":
        g_subprocess_startup_info = subprocess.STARTUPINFO()
        g_subprocess_startup_info.wShowWindow = subprocess.SW_HIDE
        g_subprocess_startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        g_creation_flags = 0x08000000  # CREATE_NO_WINDOW

    if getattr(sys, 'frozen', False):
        # Pyinstaller support
        path = os.environ["PATH"]
        if sys._MEIPASS in path:
            # already changed
            return

        tesspath = os.path.join(sys._MEIPASS, "tesseract")
        tessprefix = os.path.join(sys._MEIPASS, "data")
        logger.info("Running in packaged environment")

        if not os.path.exists(os.path.join(tessprefix, "tessdata")):
            logger.warning(
                "Running from container, but no tessdata ({}) found !".format(
                    tessprefix
                )
            )
        else:
            logger.info("TESSDATA_PREFIX set to [{}]".format(tessprefix))
            os.environ['TESSDATA_PREFIX'] = tessprefix
        if not os.path.exists(tesspath):
            logger.warning(
                "Running from container, but no tesseract ({}) found !".format(
                    tesspath
                )
            )
        else:
            logger.info("[{}] added to PATH".format(tesspath))
            os.environ['PATH'] = (
                tesspath + os.pathsep + os.environ['PATH']
            )


def can_detect_orientation():
    version = get_version()
    return (
        version[0] > 3 or
        (version[0] == 3 and version[1] >= 3)
    )


def detect_orientation(image, lang=None):
    """
    Arguments:
        image --- Pillow image to analyze
        lang --- lang to specify to tesseract

    Returns:
        {
            'angle': 90,
            'confidence': 23.73,
        }

    Raises:
        TesseractError --- if no script detected on the image
    """
    _set_environment()
    with temp_dir() as tmpdir:
        command = [TESSERACT_CMD, "input.bmp", 'stdout', "-psm", "0"]
        version = get_version()
        if version[0] >= 4:
            # XXX: temporary fix to remove once Tesseract 4 is stable
            command += ["--oem", "0"]
        if lang is not None:
            command += ['-l', lang]

        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(os.path.join(tmpdir, "input.bmp"))

        proc = subprocess.Popen(command, stdin=subprocess.PIPE, shell=False,
                                startupinfo=g_subprocess_startup_info,
                                creationflags=g_creation_flags,
                                cwd=tmpdir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        proc.stdin.close()
        original_output = proc.stdout.read()
        proc.wait()

        original_output = original_output.decode("utf-8")
        original_output = original_output.strip()

        if "Could not initialize tesseract" in original_output:
            raise TesseractError(-1, "Error initializing tesseract: %s" % original_output)

        try:
            output = original_output.split("\n")
            output = [line.split(": ", 1) for line in output if (": " in line)]
            output = {x: y for (x, y) in output}
            angle = int(output.get('Rotate', output['Orientation in degrees']))
            # Tesseract reports the angle in the opposite direction the one we
            # want
            angle = (360 - angle) % 360
            return {
                'angle': angle,
                'confidence': float(output['Orientation confidence']),
            }
        except Exception as ex:
            raise TesseractError(-1, "No script found in image (%s - %s)"
                                 % (ex.message, original_output))


def get_name():
    return "Tesseract (sh)"


def get_available_builders():
    return [
        builders.LineBoxBuilder,
        builders.TextBuilder,
        builders.WordBoxBuilder,
        CharBoxBuilder,
        builders.DigitBuilder,
    ]


def run_tesseract(input_filename, output_filename_base, cwd=None, lang=None,
                  flags=None, configs=None):
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
        cwd --- Run Tesseract in the specified working directory or use current
            one if None
        lang --- Tesseract language to use (if None, none will be specified)
        config --- List of Tesseract configs to use (if None, none will be
            specified)

    Returns:
        Returns (the exit status of Tesseract, Tesseract's output)
    '''
    _set_environment()

    command = [TESSERACT_CMD, input_filename, output_filename_base]

    if lang is not None:
        command += ['-l', lang]

    if flags is not None:
        command += flags

    if configs is not None:
        command += configs

    proc = subprocess.Popen(command, cwd=cwd,
                            startupinfo=g_subprocess_startup_info,
                            creationflags=g_creation_flags,
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


class ReOpenableTempfile(object):
    """
    On Windows, `tempfile.NamedTemporaryFile` occur Permission denied Error
    when file is still open.
    It returns `tempfile.NamedTemporaryFile` compatible object.
    """
    def __init__(self, suffix):
        self.name = None
        with tempfile.NamedTemporaryFile(prefix='tess_', suffix=suffix,
                                         delete=False) as fp:
            self.name = fp.name

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        if self.name is not None:
            os.remove(self.name)
            self.name = None


@contextlib.contextmanager
def temp_dir():
    """
    A context manager for maintaining a temporary directory
    """
    # NOTE: Drop this as soon as we don't support Python 2.7 anymore, because
    # since Python 3.2 there is a context manager called TemporaryDirectory().
    path = tempfile.mkdtemp(prefix='tess_')
    try:
        yield path
    finally:
        shutil.rmtree(path)


def image_to_string(image, lang=None, builder=None):
    '''
    Runs tesseract on the specified image. First, the image is written to disk,
    and then the tesseract command is run on the image. Tesseract's result is
    read, and the temporary files are erased.

    Arguments:
        image --- image to OCR.
        lang --- tesseract language to use.
        builder --- builder used to configure Tesseract and read its result.
            The builder is used to specify the type of output expected.
            Possible builders are TextBuilder or CharBoxBuilder. If builder ==
            None, the builder used will be TextBuilder.

    Returns:
        Depends of the specified builder. By default, it will return a simple
        string.
    '''

    if builder is None:
        builder = builders.TextBuilder()
    with temp_dir() as tmpdir:
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(os.path.join(tmpdir, "input.bmp"))
        (status, errors) = run_tesseract("input.bmp", "output", cwd=tmpdir,
                                         lang=lang,
                                         flags=builder.tesseract_flags,
                                         configs=builder.tesseract_configs)
        if status:
            raise TesseractError(status, errors)

        output_file_name = "ERROR"
        for file_extension in builder.file_extensions:
            output_file_name = ('%s.%s' % (os.path.join(tmpdir, "output"),
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
    _set_environment()
    return util.is_on_path(TESSERACT_CMD)


def get_available_languages():
    """
    Returns the list of languages that Tesseract knows how to handle.

    Returns:
        An array of strings. Note that most languages name conform to ISO 639
        terminology, but not all. Most of the time, truncating the language
        name name returned by this function to 3 letters should do the trick.
    """
    _set_environment()
    proc = subprocess.Popen([TESSERACT_CMD, "--list-langs"],
                            startupinfo=g_subprocess_startup_info,
                            creationflags=g_creation_flags,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    langs = proc.stdout.read().decode('utf-8').splitlines(False)
    ret = proc.wait()
    if ret != 0:
        raise TesseractError(ret, "unable to get languages")

    return [lang for lang in langs if lang and lang[-1] != ':']


def get_version():
    """
    Returns Tesseract version.

    Returns:
        A tuple corresponding to the version (for instance, (3, 0, 1) for 3.01)

    Exception:
        TesseractError --- Unable to run tesseract or to parse the version
    """
    _set_environment()

    command = [TESSERACT_CMD, "-v"]

    proc = subprocess.Popen(command,
                            startupinfo=g_subprocess_startup_info,
                            creationflags=g_creation_flags,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    ver_string = proc.stdout.read()
    ver_string = ver_string.decode('utf-8')
    ret = proc.wait()
    if ret not in (0, 1):
        raise TesseractError(ret, ver_string)

    try:
        ver_string = ver_string.split(" ")[1]
        index = ver_string.find("dev")
        if index:
            ver_string = ver_string[:index]

        els = ver_string.split(".")
        els = [digits_only(x) for x in els]
        major = els[0]
        minor = els[1]
        upd = 0
        if len(els) >= 3:
            upd = els[2]
        return (major, minor, upd)
    except IndexError:
        raise TesseractError(
            ret, ("Unable to parse Tesseract version (spliting failed): [%s]"
                  % (ver_string)))
    except ValueError:
        raise TesseractError(
            ret, ("Unable to parse Tesseract version (not a number): [%s]"
                  % (ver_string)))
