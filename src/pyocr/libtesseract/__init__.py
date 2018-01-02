#!/usr/bin/env python3
'''
libtesseract/ is a wrapper for google's Tesseract-OCR C API
( http://code.google.com/p/tesseract-ocr/ ).

USAGE:
 > from PIL import Image
 > from pyocr.libtesseract import image_to_string
 > print(image_to_string(Image.open('test.png')))
 > print(image_to_string(Image.open('test-european.jpg'), lang='fra'))

COPYRIGHT:
PyOCR is released under the GPL v3.
Copyright (c) Jerome Flesch, 2011-2016
https://github.com/openpaperwork/pyocr#readme
'''
from os import devnull
from .. import builders
from . import tesseract_raw
from ..error import TesseractError
from ..util import digits_only


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
            raise TesseractError(
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
        # XXX(Jflesch): Issue #51:
        # Tesseract TessBaseAPIRecognize() may segfault when the target
        # language is not available
        clang = lang if lang else "eng"
        for lang_item in clang.split("+"):
            if lang_item not in tesseract_raw.get_available_languages(handle):
                raise TesseractError(
                    "no lang",
                    "language {} is not available".format(lang_item)
                )

        tesseract_raw.set_page_seg_mode(
            handle, builder.tesseract_layout
        )
        tesseract_raw.set_debug_file(handle, devnull)

        tesseract_raw.set_image(handle, image)
        if "digits" in builder.tesseract_configs:
            tesseract_raw.set_is_numeric(handle, True)
        # XXX(JFlesch): PageIterator and ResultIterator are actually the
        # very same thing. If it changes, we are screwed.
        tesseract_raw.recognize(handle)
        res_iterator = tesseract_raw.get_iterator(handle)
        if res_iterator is None:
            raise TesseractError(
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

            last_word_in_line = tesseract_raw.page_iterator_is_at_final_element(
                page_iterator, lvl_line, lvl_word
            )

            word = tesseract_raw.result_iterator_get_utf8_text(
                res_iterator, lvl_word
            )

            confidence = tesseract_raw.result_iterator_get_confidence(
                res_iterator, lvl_word
            )

            if word is not None and confidence is not None and word != "":
                (r, box) = tesseract_raw.page_iterator_bounding_box(
                    page_iterator, lvl_word
                )
                assert(r)
                box = _tess_box_to_pyocr_box(box)
                builder.add_word(word, box, confidence)

                if last_word_in_line:
                    builder.end_line()

            if not tesseract_raw.page_iterator_next(page_iterator, lvl_word):
                break

    finally:
        tesseract_raw.cleanup(handle)

    return builder.get_output()


def image_to_pdf(image, output_file, lang=None, input_file="stdin", textonly=False):
    '''
    Creates pdf file with embeded text based on OCR from an image

    Args:
        image: image to be converted
        output_file: path to the file that will be created, `.pdf` extension
            should not be specified
        lang: three letter language code. For available languages see
            https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc#languages.
            Defaults to None.
        input_file: path to the image file that should be beneath the text in
            output pdf. If not specified (stdin, incorrect file) output pdf is
            correct but tesseract writes some errors about not being able to
            open the file. Defaults to stdin.
        textonly: create pdf with only one invisible text layer. Defaults to
            False.
    '''
    handle = tesseract_raw.init(lang=lang)
    renderer = None
    try:
        tesseract_raw.set_image(handle, image)
        tesseract_raw.set_page_seg_mode(
            handle, tesseract_raw.PageSegMode.AUTO_OSD
        )

        tesseract_raw.set_input_name(handle, input_file)
        tesseract_raw.recognize(handle)

        renderer = tesseract_raw.init_pdf_renderer(
            handle, output_file, textonly
        )
        assert(renderer)

        tesseract_raw.begin_document(renderer, "")
        tesseract_raw.add_renderer_image(handle, renderer)
        tesseract_raw.end_document(renderer)
    finally:
        tesseract_raw.cleanup(handle)
        if renderer:
            tesseract_raw.cleanup(renderer)


def is_available():
    available = tesseract_raw.is_available()
    if not available:
        return False
    version = get_version()

    # C-API with Tesseract <= 3.02 segfaults sometimes
    # (seen with Debian stable + Paperwork)
    # not tested with 3.03
    if (version[0] < 3 or
            (version[0] == 3 and version[1] < 4)):
        print("Unsupported version [%s]" % ".".join([str(r) for r in version]))
        return False
    return True


def get_available_languages():
    handle = tesseract_raw.init()
    try:
        return tesseract_raw.get_available_languages(handle)
    finally:
        tesseract_raw.cleanup(handle)


def get_version():
    version = tesseract_raw.get_version()
    version = version.split(" ", 1)[0]

    # cut off "dev" string if exists for proper int conversion
    index = version.find("dev")
    if index != -1:
        version = version[:index]

    version = version.split(".")
    major = digits_only(version[0])
    minor = digits_only(version[1])
    upd = 0
    if len(version) >= 3:
        upd = digits_only(version[2])
    return (major, minor, upd)
