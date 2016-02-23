import ctypes
import os
import sys

TESSDATA_PREFIX = os.getenv('TESSDATA_PREFIX', None)

if sys.platform[:3] == "win":
    libnames = [
        # Jflesch> Don't they have the equivalent of LD_LIBRARY_PATH on
        # Windows ?
        "../vs2010/DLL_Release/libtesseract302.dll",
        "libtesseract302.dll",
    ]
else:
    libnames = [
        "libtesseract.so.3",
    ]


g_libtesseract = None

for libname in libnames:
    try:
        g_libtesseract = ctypes.cdll.LoadLibrary(libname)
    except OSError:
        pass

if g_libtesseract:
    g_libtesseract.TessVersion.argtypes = []
    g_libtesseract.TessVersion.restype = ctypes.c_char_p

    g_libtesseract.TessBaseAPICreate.argtypes = []
    g_libtesseract.TessBaseAPICreate.restype = ctypes.c_void_p  # TessBaseAPI*
    g_libtesseract.TessBaseAPIDelete.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
    ]
    g_libtesseract.TessBaseAPIDelete.argtypes = None

    g_libtesseract.TessBaseAPIInit3.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
        ctypes.c_char_p,  # datapath
        ctypes.c_char_p,  # language
    ]
    g_libtesseract.TessBaseAPIInit3.restype = ctypes.c_int

    g_libtesseract.TessBaseAPIGetAvailableLanguagesAsVector.argtypes = [
        ctypes.c_void_p  # TessBaseAPI*
    ]
    g_libtesseract.TessBaseAPIGetAvailableLanguagesAsVector.restype = \
        ctypes.POINTER(ctypes.c_char_p)

    g_libtesseract.TessBaseAPISetPageSegMode.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
        ctypes.c_int,  # See PageSegMode
    ]
    g_libtesseract.TessBaseAPISetPageSegMode.restype = None

    g_libtesseract.TessBaseAPIInitForAnalysePage.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
    ]
    g_libtesseract.TessBaseAPIInitForAnalysePage.restype = None

    g_libtesseract.TessBaseAPISetImage.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
        ctypes.POINTER(ctypes.c_char),  # imagedata
        ctypes.c_int,  # width
        ctypes.c_int,  # height
        ctypes.c_int,  # bytes_per_pixel
        ctypes.c_int,  # bytes_per_line
    ]
    g_libtesseract.TessBaseAPISetImage.restype = None

    g_libtesseract.TessBaseAPIRecognize.argstypes = [
        ctypes.c_void_p,  # TessBaseAPI*
        ctypes.c_void_p,  # ETEXT_DESC*
    ]
    g_libtesseract.TessBaseAPIRecognize.restype = ctypes.c_int

    g_libtesseract.TessBaseAPIAnalyseLayout.argstypes = [
        ctypes.c_void_p,  # TessBaseAPI*
    ]
    g_libtesseract.TessBaseAPIAnalyseLayout.restype = \
        ctypes.c_void_p  # TessPageIterator*

    g_libtesseract.TessBaseAPIGetUTF8Text.argstype = [
        ctypes.c_void_p,  # TessBaseAPI*
    ]
    g_libtesseract.TessBaseAPIGetUTF8Text.restype = ctypes.c_char_p

    g_libtesseract.TessPageIteratorDelete.argstypes = [
        ctypes.c_void_p,  # TessPageIterator*
    ]
    g_libtesseract.TessPageIteratorDelete.restype = None

    g_libtesseract.TessPageIteratorOrientation.argstype = [
        ctypes.c_void_p,  # TessPageIterator*
        ctypes.POINTER(ctypes.c_int),  # TessOrientation*
        ctypes.POINTER(ctypes.c_int),  # TessWritingDirection*
        ctypes.POINTER(ctypes.c_int),  # TessTextlineOrder*
        ctypes.POINTER(ctypes.c_float),  # deskew_angle
    ]
    g_libtesseract.TessPageIteratorOrientation.restype = None


class PageSegMode(object):
    OSD_ONLY = 0
    AUTO_OSD = 1
    AUTO_ONLY = 2
    AUTO = 3
    SINGLE_COLUMN = 4
    SINGLE_BLOCK_VERT_TEXT = 5
    SINGLE_BLOCK = 6
    SINGLE_LINE = 7
    SINGLE_WORD = 8
    CIRCLE_WORD = 9
    SINGLE_CHAR = 10
    SPARSE_TEXT = 11
    SPARSE_TEXT_OSD = 12
    COUNT = 13


class Orientation(object):
    PAGE_UP = 0
    PAGE_RIGHT = 1
    PAGE_DOWN = 2
    PAGE_LEFT = 3


def init(lang=None):
    assert(g_libtesseract)
    handle = g_libtesseract.TessBaseAPICreate()
    try:
        if lang:
            lang = lang.encode("utf-8")
        prefix = None
        if TESSDATA_PREFIX:
            prefix = TESSDATA_PREFIX.encode("utf-8")
        g_libtesseract.TessBaseAPIInit3(
            handle,
            ctypes.c_char_p(prefix),
            ctypes.c_char_p(lang)
        )
    except:
        g_libtesseract.TessBaseAPIDelete(handle)
        raise
    return handle


def cleanup(handle):
    g_libtesseract.TessBaseAPIDelete(handle)


def is_available():
    global g_libtesseract
    return g_libtesseract is not None


def get_version():
    global g_libtesseract
    assert(g_libtesseract)

    return g_libtesseract.TessVersion().decode("utf-8")


def get_available_languages(handle):
    global g_libtesseract
    assert(g_libtesseract)

    langs = []
    c_langs = g_libtesseract.TessBaseAPIGetAvailableLanguagesAsVector(
        handle
    )
    i = 0
    while c_langs[i]:
        langs.append(c_langs[i].decode("utf-8"))
        i += 1

    return langs


def set_page_seg_mode(handle, mode):
    global g_libtesseract
    assert(g_libtesseract)

    g_libtesseract.TessBaseAPISetPageSegMode(
        handle, ctypes.c_int(mode)
    )


def init_for_analyse_page(handle):
    global g_libtesseract
    assert(g_libtesseract)

    g_libtesseract.TessBaseAPIInitForAnalysePage(handle)


def set_image(handle, image):
    global g_libtesseract
    assert(g_libtesseract)

    image = image.convert("RGB")
    image.load()
    imgdata = image.tobytes()

    imgsize = image.size

    g_libtesseract.TessBaseAPISetImage(
        handle,
        imgdata,
        ctypes.c_int(imgsize[0]),
        ctypes.c_int(imgsize[1]),
        ctypes.c_int(3),  # RGB = 3 * 8
        ctypes.c_int(imgsize[0] * 3)
    )


def recognize(handle):
    global g_libtesseract
    assert(g_libtesseract)

    return g_libtesseract.TessBaseAPIRecognize(handle, ctypes.c_void_p(None))


def analyse_layout(handle):
    global g_libtesseract
    assert(g_libtesseract)

    return g_libtesseract.TessBaseAPIAnalyseLayout(handle)


def get_utf8_text(handle):
    return g_libtesseract.TessBaseAPIGetUTF8Text(handle).decode("utf-8")


def page_iterator_delete(iterator):
    global g_libtesseract
    assert(g_libtesseract)

    return g_libtesseract.TessPageIteratorDelete(iterator)


def page_iterator_orientation(iterator):
    global g_libtesseract
    assert(g_libtesseract)

    orientation = ctypes.c_int(0)
    writing_direction = ctypes.c_int(0)
    textline_order = ctypes.c_int(0)
    deskew_angle = ctypes.c_float(0.0)

    g_libtesseract.TessPageIteratorOrientation(
        iterator,
        ctypes.POINTER(orientation),
        ctypes.POINTER(writing_direction),
        ctypes.POINTER(textline_order),
        ctypes.POINTER(deskew_angle)
    )

    return {
        "orientation": orientation.value,
        "writing_direction": writing_direction.value,
        "textline_order": textline_order.value,
        "deskew_angle": deskew_angle.value,
    }
