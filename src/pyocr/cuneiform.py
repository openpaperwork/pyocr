#!/usr/bin/env python
'''
cuneiform.py is a wrapper for Cuneiform

USAGE:
 > from PIL import Image
 > from pyocr.cuneiform import image_to_string
 > print image_to_string(Image.open('test.png'))
 > print image_to_string(Image.open('test-european.jpg'), lang='fra')

COPYRIGHT:
PyOCR is released under the GPL v3.
Copyright (c) Samuel Hoffstaetter, 2009
Copyright (c) Jerome Flesch, 2011-2016
https://github.com/jflesch/python-tesseract#readme
'''

import codecs
from io import BytesIO
import os
import re
import subprocess
import tempfile

from . import builders
from . import util


# CHANGE THIS IF CUNEIFORM IS NOT IN YOUR PATH, OR IS NAMED DIFFERENTLY
CUNEIFORM_CMD = 'cuneiform'

CUNEIFORM_DATA_POSSIBLE_PATHS = [
    "/usr/local/share/cuneiform",
    "/usr/share/cuneiform",
]

LANGUAGES_LINE_PREFIX = "Supported languages: "
LANGUAGES_SPLIT_RE = re.compile("[^a-z]")
VERSION_LINE_RE = re.compile("Cuneiform for \w+ (\d+).(\d+).(\d+)")

__all__ = [
    'can_detect_orientation',
    'get_available_builders',
    'get_available_languages',
    'get_name',
    'get_version',
    'image_to_string',
    'is_available',
    'CuneiformError',
]


def can_detect_orientation():
    return False


def get_name():
    return "Cuneiform (sh)"


def get_available_builders():
    return [
        builders.TextBuilder,
        builders.WordBoxBuilder,
    ]


class CuneiformError(Exception):
    def __init__(self, status, message):
        Exception.__init__(self, message)
        self.status = status
        self.message = message
        self.args = (status, message)


def temp_file(suffix):
    ''' Returns a temporary file '''
    return tempfile.NamedTemporaryFile(prefix='cuneiform_', suffix=suffix)


def cleanup(filename):
    ''' Tries to remove the given filename. Ignores non-existent files '''
    try:
        os.remove(filename)
    except OSError:
        pass


def image_to_string(image, lang=None, builder=None):
    if builder is None:
        builder = builders.TextBuilder()

    with temp_file(builder.file_extensions[0]) as output_file:
        cmd = [CUNEIFORM_CMD]
        if lang is not None:
            cmd += ["-l", lang]
        cmd += builder.cuneiform_args
        cmd += ["-o", output_file.name]
        cmd += ["-"]  # stdin

        if image.mode != "RGB":
            image = image.convert("RGB")

        img_data = BytesIO()
        image.save(img_data, format="BMP")

        proc = subprocess.Popen(cmd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        proc.stdin.write(img_data.getvalue())
        proc.stdin.close()
        output = proc.stdout.read().decode('utf-8')
        retcode = proc.wait()
        if retcode:
            raise CuneiformError(retcode, output)
        with codecs.open(output_file.name, 'r', encoding='utf-8',
                         errors='replace') as file_desc:
            results = builder.read_file(file_desc)
        return results


def is_available():
    return util.is_on_path(CUNEIFORM_CMD)


def get_available_languages():
    proc = subprocess.Popen([CUNEIFORM_CMD, "-l"], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    output = proc.stdout.read().decode('utf-8')
    proc.wait()
    languages = []
    for line in output.split("\n"):
        if not line.startswith(LANGUAGES_LINE_PREFIX):
            continue
        line = line[len(LANGUAGES_LINE_PREFIX):]
        for language in LANGUAGES_SPLIT_RE.split(line):
            if language == "":
                continue
            languages.append(language)
    return languages


def get_version():
    proc = subprocess.Popen([CUNEIFORM_CMD], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    output = proc.stdout.read().decode('utf-8')
    proc.wait()
    for line in output.split("\n"):
        m = VERSION_LINE_RE.match(line)
        g = m.groups()
        if m is not None:
            ver = (int(g[0]), int(g[1]), int(g[2]))
            return ver
    return None
