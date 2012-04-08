#!/usr/bin/env python2

import codecs
import os
import re
import StringIO
import subprocess
import sys

import builders
import util


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
    'get_available_builders',
    'get_available_languages',
    'get_name',
    'get_version',
    'image_to_string',
    'is_available',
    'CuneiformError',
]


def get_name():
    return "Cuneiform"


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


def tempnam():
    ''' Returns a temporary file-name '''
    # prevent os.tempnam from printing an error
    stderr = sys.stderr
    try:
        sys.stderr = StringIO.StringIO()
        return os.tempnam(None, 'cuneiform_')
    finally:
        sys.stderr = stderr


def cleanup(filename):
    ''' Tries to remove the given filename. Ignores non-existent files '''
    try:
        os.remove(filename)
    except OSError:
        pass


def image_to_string(image, lang=None, builder=None):
    if builder == None:
        builder = builders.TextBuilder()

    output_file_name_base = tempnam()
    output_file_name = ('%s.%s' % (output_file_name_base,
                                   builder.file_extension))

    cmd = [ CUNEIFORM_CMD ]
    if lang != None:
        cmd += [ "-l", lang ]
    cmd += builder.cuneiform_args
    cmd += [ "-o", output_file_name ]
    cmd += [ "-" ] # stdin

    try:
        img_data = StringIO.StringIO()
        image.save(img_data, format="png")

        proc = subprocess.Popen(cmd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        proc.stdin.write(img_data.getvalue())
        proc.stdin.close()
        output = proc.stdout.read()
        retcode = proc.wait()
        if retcode:
            raise CuneiformError(retcode, output)
        with codecs.open(output_file_name, 'r', encoding='utf-8') as file_desc:
            results = builder.read_file(file_desc)
        return results
    finally:
        cleanup(output_file_name)


def is_available():
    return util.is_on_path(CUNEIFORM_CMD)



def get_available_languages():
    proc = subprocess.Popen([ CUNEIFORM_CMD, "-l" ], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    output = proc.stdout.read()
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
    proc = subprocess.Popen([ CUNEIFORM_CMD ], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    output = proc.stdout.read()
    proc.wait()
    for line in output.split("\n"):
        m = VERSION_LINE_RE.match(line)
        g = m.groups()
        if m != None:
            ver = (int(g[0]), int(g[1]), int(g[2]))
            return ver
    return None
