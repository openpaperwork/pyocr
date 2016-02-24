#!/usr/bin/env python3
'''
tesseract_capi/ is a wrapper for google's Tesseract-OCR C API
( http://code.google.com/p/tesseract-ocr/ ).

USAGE:
 > from PIL import Image
 > from pyocr.tesseract_api import image_to_string
 > print(image_to_string(Image.open('test.png')))
 > print(image_to_string(Image.open('test-european.jpg'), lang='fra'))

COPYRIGHT:
PyOCR is released under the GPL v3.
Copyright (c) Jerome Flesch, 2011-2012
https://github.com/jflesch/pyocr#readme
'''
import sys

from .. import builders

from . import tesseract_raw


__all__ = [
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


def can_detect_orientation():
    return True


def detect_orientation(image, lang=None):
    handle = tesseract_raw.init(lang=lang)
    try:
        tesseract_raw.set_page_seg_mode(
            handle, tesseract_raw.PageSegMode.OSD_ONLY
        )
        tesseract_raw.set_image(handle, image)
        os = tesseract_raw.detect_os(handle)
        if os['confidence'] <= 0:
            raise tesseract_raw.TesseractError(
                "no script", "no script detected"
            )
        orientation = {
            tesseract_raw.Orientation.PAGE_UP: 0,
            tesseract_raw.Orientation.PAGE_RIGHT: 90,
            tesseract_raw.Orientation.PAGE_DOWN: 180,
            tesseract_raw.Orientation.PAGE_LEFT: 270,
        }[os['orientation']]
        return {
            'angle': orientation,
            'confidence': os['confidence']
        }
    finally:
        tesseract_raw.cleanup(handle)


def get_name():
    return "Tesseract (C-API)"


def get_available_builders():
    return [
        builders.TextBuilder,
        builders.WordBoxBuilder,
    ]


def _tess_box_to_pyocr_box(box):
    return (
        (box[0], box[1]),
        (box[2], box[3]),
    )


def image_to_string(image, lang=None, builder=None):
    if builder is None:
        builder = builders.TextBuilder()
    handle = tesseract_raw.init(lang=lang)

    lvl_line = tesseract_raw.PageIteratorLevel.TEXTLINE
    lvl_word = tesseract_raw.PageIteratorLevel.WORD

    try:
        if builder.tesseract_layout != tesseract_raw.PageSegMode.AUTO:
            tesseract_raw.set_page_seg_mode(
                handle, builder.tesseract_layout
            )

        tesseract_raw.set_image(handle, image)

        # XXX(JFlesch): PageIterator and ResultIterator are actually the
        # very same thing. If it changes, we are screwed.
        tesseract_raw.recognize(handle)
        res_iterator = tesseract_raw.get_iterator(handle)
        if res_iterator is None:
            raise tesseract_raw.TesseractError(
                "no script", "no script detected"
            )
        page_iterator = tesseract_raw.result_iterator_get_page_iterator(
            res_iterator
        )

        while True:
            if tesseract_raw.page_iterator_is_at_beginning_of(
                    page_iterator, lvl_line):
                (r, box) = tesseract_raw.page_iterator_bounding_box(
                    page_iterator, lvl_line
                )
                assert(r)
                box = _tess_box_to_pyocr_box(box)
                builder.start_line(box)

            word = tesseract_raw.result_iterator_get_utf8_text(
                res_iterator, lvl_word
            )
            (r, box) = tesseract_raw.page_iterator_bounding_box(
                page_iterator, lvl_word
            )
            assert(r)
            box = _tess_box_to_pyocr_box(box)
            builder.add_word(word, box)

            if tesseract_raw.page_iterator_is_at_final_element(
                    page_iterator, lvl_line, lvl_word):
                builder.end_line()

            if not tesseract_raw.page_iterator_next(page_iterator, lvl_word):
                break

    finally:
        tesseract_raw.cleanup(handle)

    return builder.get_output()


def is_available():
    # We limit to Python 3. Supporting both Python 2.7 and Python 3.x
    # would be too hard
    python_ver = (sys.version_info[0], sys.version_info[1])
    if python_ver < (3, 0):
        return False
    return tesseract_raw.is_available()


def get_available_languages():
    handle = tesseract_raw.init()
    try:
        return tesseract_raw.get_available_languages(handle)
    finally:
        tesseract_raw.cleanup(handle)


def get_version():
    version = tesseract_raw.get_version()
    version = version.split(" ", 1)[0]
    version = version.split(".")
    major = int(version[0])
    minor = int(version[1])
    upd = 0
    if len(version) >= 3:
        upd = int(version[2])
    return (major, minor, upd)
