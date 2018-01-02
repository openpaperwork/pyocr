import ctypes
import logging
import os
import sys

from ..error import TesseractError


logger = logging.getLogger(__name__)

TESSDATA_PREFIX = os.getenv('TESSDATA_PREFIX', None)
libnames = []

if getattr(sys, 'frozen', False):
    # Pyinstaller integration
    libnames += [os.path.join(sys._MEIPASS, "libtesseract-4.dll")]
    libnames += [os.path.join(sys._MEIPASS, "libtesseract-3.dll")]
    tessdata = os.path.join(sys._MEIPASS, "data")
    if not os.path.exists(os.path.join(tessdata, "tessdata")):
        logger.warning(
            "Running from container, but no tessdata ({}) found !".format(
                tessdata
            )
        )
    else:
        TESSDATA_PREFIX = tessdata


if sys.platform[:3] == "win":
    libnames += [
        # Jflesch> Don't they have the equivalent of LD_LIBRARY_PATH on
        # Windows ?
        "../vs2010/DLL_Release/libtesseract302.dll",
        "libtesseract302.dll",
        "C:\\Program Files (x86)\\Tesseract-OCR\\libtesseract-4.dll",
        "C:\\Program Files (x86)\\Tesseract-OCR\\libtesseract-3.dll",
    ]
else:
    libnames += [
        "libtesseract.so.4",
        "libtesseract.so.3",
    ]


g_libtesseract = None

lib_load_errors = []
for libname in libnames:
    try:
        g_libtesseract = ctypes.cdll.LoadLibrary(libname)
        lib_load_errors = []
        break
    except OSError as ex:
        lib_load_errors.append((libname, ex.message))


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


class PageIteratorLevel(object):
    BLOCK = 0
    PARA = 1
    TEXTLINE = 2
    WORD = 3
    SYMBOL = 4


class PolyBlockType(object):
    UNKNOWN = 0
    FLOWING_TEXT = 1
    HEADING_TEXT = 2
    PULLOUT_TEXT = 3
    TABLE = 4
    VERTICAL_TEXT = 5
    CAPTION_TEXT = 6
    FLOWING_IMAGE = 7
    HEADING_IMAGE = 8
    PULLOUT_IMAGE = 9
    HORZ_LINE = 10
    VERT_LINE = 11
    NOISE = 12
    COUNT = 13


class OSResults(ctypes.Structure):
    _fields_ = [
        ("orientations", ctypes.c_float * 4),
        ("scripts_na", ctypes.c_float * 4 * (116 + 1 + 2 + 1)),
        ("unicharset", ctypes.c_void_p),
        ("best_orientation_id", ctypes.c_int),
        ("best_script_id", ctypes.c_int),
        ("best_sconfidence", ctypes.c_float),
        ("best_oconfidence", ctypes.c_float),
        # extra padding in case the structure is extended later
        ("padding", ctypes.c_char * 512),
    ]


if g_libtesseract:
    g_libtesseract.TessVersion.argtypes = []
    g_libtesseract.TessVersion.restype = ctypes.c_char_p

    g_libtesseract.TessBaseAPICreate.argtypes = []
    g_libtesseract.TessBaseAPICreate.restype = ctypes.c_void_p  # TessBaseAPI*
    g_libtesseract.TessBaseAPIDelete.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
    ]
    g_libtesseract.TessBaseAPIDelete.argtypes = None

    g_libtesseract.TessBaseAPIGetDatapath.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
    ]
    g_libtesseract.TessBaseAPIGetDatapath.restype = ctypes.POINTER(
        ctypes.c_char)

    g_libtesseract.TessBaseAPIInit1.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
        ctypes.c_char_p,  # datapath
        ctypes.c_char_p,  # language
        ctypes.c_int,  # TessOcrEngineMode
        ctypes.POINTER(ctypes.c_char_p),  # configs
        ctypes.c_int,  # configs_size
    ]
    g_libtesseract.TessBaseAPIInit1.restype = ctypes.c_int

    g_libtesseract.TessBaseAPIInit3.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
        ctypes.c_char_p,  # datapath
        ctypes.c_char_p,  # language
    ]
    g_libtesseract.TessBaseAPIInit3.restype = ctypes.c_int

    g_libtesseract.TessBaseAPISetVariable.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
        ctypes.c_char_p,  # name
        ctypes.c_char_p,  # value
    ]
    g_libtesseract.TessBaseAPISetVariable.restype = ctypes.c_bool

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

    g_libtesseract.TessResultRendererAddImage.argtypes = [
        ctypes.c_void_p,  # TessResultRenderer* renderer
        ctypes.c_void_p  # TessBaseAPI* api
    ]
    g_libtesseract.TessResultRendererAddImage.restype = ctypes.c_bool

    g_libtesseract.TessBaseAPISetInputName.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI* handle
        ctypes.c_char_p  # const char* name
    ]
    g_libtesseract.TessBaseAPISetInputName.restype = None

    g_libtesseract.TessResultRendererBeginDocument.argtypes = [
        ctypes.c_void_p,  # TessResultRenderer* renderer
        ctypes.c_char_p  # const char* title
    ]
    g_libtesseract.TessResultRendererBeginDocument.restype = ctypes.c_bool

    g_libtesseract.TessResultRendererEndDocument.argtypes = [
        ctypes.c_void_p  # TessResultRenderer* renderer
    ]
    g_libtesseract.TessResultRendererEndDocument.restype = ctypes.c_bool

    g_libtesseract.TessPDFRendererCreate.argtypes = [
        ctypes.c_char_p,  # const char* outputbase
        ctypes.c_char_p,  # const char* datadir
        ctypes.c_bool  # BOOL textonly
    ]
    g_libtesseract.TessPDFRendererCreate.restype = ctypes.c_void_p

    g_libtesseract.TessBaseAPIRecognize.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
        ctypes.c_void_p,  # ETEXT_DESC*
    ]
    g_libtesseract.TessBaseAPIRecognize.restype = ctypes.c_int

    g_libtesseract.TessBaseAPIGetIterator.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
    ]
    g_libtesseract.TessBaseAPIGetIterator.restype = \
        ctypes.c_void_p  # TessResultIterator

    g_libtesseract.TessBaseAPIAnalyseLayout.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
    ]
    g_libtesseract.TessBaseAPIAnalyseLayout.restype = \
        ctypes.c_void_p  # TessPageIterator*

    g_libtesseract.TessBaseAPIGetUTF8Text.argtypes = [
        ctypes.c_void_p,  # TessBaseAPI*
    ]
    g_libtesseract.TessBaseAPIGetUTF8Text.restype = ctypes.c_void_p

    g_libtesseract.TessPageIteratorDelete.argtypes = [
        ctypes.c_void_p,  # TessPageIterator*
    ]
    g_libtesseract.TessPageIteratorDelete.restype = None

    g_libtesseract.TessPageIteratorOrientation.argtypes = [
        ctypes.c_void_p,  # TessPageIterator*
        ctypes.POINTER(ctypes.c_int),  # TessOrientation*
        ctypes.POINTER(ctypes.c_int),  # TessWritingDirection*
        ctypes.POINTER(ctypes.c_int),  # TessTextlineOrder*
        ctypes.POINTER(ctypes.c_float),  # deskew_angle
    ]
    g_libtesseract.TessPageIteratorOrientation.restype = None

    g_libtesseract.TessPageIteratorNext.argtypes = [
        ctypes.c_void_p,  # TessPageIterator*
        ctypes.c_int,  # TessPageIteratorLevel
    ]
    g_libtesseract.TessPageIteratorNext.restype = ctypes.c_bool

    g_libtesseract.TessPageIteratorIsAtBeginningOf.argtypes = [
        ctypes.c_void_p,  # TessPageIterator*
        ctypes.c_int,  # TessPageIteratorLevel
    ]
    g_libtesseract.TessPageIteratorIsAtBeginningOf.restype = ctypes.c_bool

    g_libtesseract.TessPageIteratorIsAtFinalElement.argtypes = [
        ctypes.c_void_p,  # TessPageIterator*
        ctypes.c_int,  # TessPageIteratorLevel (level)
        ctypes.c_int,  # TessPageIteratorLevel (element)
    ]
    g_libtesseract.TessPageIteratorIsAtFinalElement.restype = ctypes.c_bool

    g_libtesseract.TessPageIteratorBlockType.argtypes = [
        ctypes.c_void_p,  # TessPageIterator*
    ]
    g_libtesseract.TessPageIteratorBlockType.restype = \
        ctypes.c_int  # PolyBlockType

    g_libtesseract.TessPageIteratorBoundingBox.args = [
        ctypes.c_void_p,  # TessPageIterator*
        ctypes.c_int,  # TessPageIteratorLevel (level)
        ctypes.POINTER(ctypes.c_int),  # left
        ctypes.POINTER(ctypes.c_int),  # top
        ctypes.POINTER(ctypes.c_int),  # right
        ctypes.POINTER(ctypes.c_int),  # bottom
    ]
    g_libtesseract.TessPageIteratorBoundingBox.restype = ctypes.c_bool

    g_libtesseract.TessResultIteratorGetPageIterator.argtypes = [
        ctypes.c_void_p,  # TessResultIterator*
    ]
    g_libtesseract.TessResultIteratorGetPageIterator.restype = \
        ctypes.c_void_p  # TessPageIterator*

    g_libtesseract.TessResultIteratorGetUTF8Text.argtypes = [
        ctypes.c_void_p,  # TessResultIterator*
        ctypes.c_int,  # TessPageIteratorLevel (level)
    ]
    g_libtesseract.TessResultIteratorGetUTF8Text.restype = \
        ctypes.c_void_p

    g_libtesseract.TessResultIteratorConfidence.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
    ]
    g_libtesseract.TessResultIteratorConfidence.restype = ctypes.c_float

    g_libtesseract.TessDeleteText.argtypes = [
        ctypes.c_void_p
    ]
    g_libtesseract.TessDeleteText.restype = None

    if hasattr(g_libtesseract, 'TessBaseAPIDetectOrientationScript'):
        g_libtesseract.TessBaseAPIDetectOrientationScript.argtypes = [
            ctypes.c_void_p,  # TessBaseAPI*
            ctypes.POINTER(ctypes.c_int),  # orient_deg
            ctypes.POINTER(ctypes.c_float),  # orient_conf
            ctypes.POINTER(ctypes.c_char_p),  # script_name
            ctypes.POINTER(ctypes.c_float),  # script_conf
        ]
        g_libtesseract.TessBaseAPIDetectOrientationScript.restype = \
            ctypes.c_bool
    else:
        g_libtesseract.TessBaseAPIDetectOS.argtypes = [
            ctypes.c_void_p,  # TessBaseAPI*
            ctypes.POINTER(OSResults),
        ]
        g_libtesseract.TessBaseAPIDetectOS.restype = ctypes.c_bool


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
            ctypes.c_void_p(handle),
            ctypes.c_char_p(prefix),
            ctypes.c_char_p(lang)
        )
        g_libtesseract.TessBaseAPISetVariable(
            ctypes.c_void_p(handle),
            b"tessedit_zero_rejection",
            b"F"
        )
    except:
        g_libtesseract.TessBaseAPIDelete(ctypes.c_void_p(handle))
        raise
    return handle


def cleanup(handle):
    assert(g_libtesseract)
    g_libtesseract.TessBaseAPIDelete(ctypes.c_void_p(handle))


def is_available():
    return g_libtesseract is not None


def get_version():
    assert(g_libtesseract)
    return g_libtesseract.TessVersion().decode("utf-8")


def get_available_languages(handle):
    assert(g_libtesseract)

    langs = []
    c_langs = g_libtesseract.TessBaseAPIGetAvailableLanguagesAsVector(
        ctypes.c_void_p(handle)
    )
    i = 0
    while c_langs[i]:
        langs.append(c_langs[i].decode("utf-8"))
        i += 1

    return langs


def set_is_numeric(handle, mode):
    assert(g_libtesseract)

    if mode:
        wl = b"0123456789."
    else:
        wl = b""

    g_libtesseract.TessBaseAPISetVariable(
        ctypes.c_void_p(handle),
        b"tessedit_char_whitelist",
        wl
    )


def set_debug_file(handle, filename):
    assert(g_libtesseract)

    if not isinstance(filename, bytes):
        filename = filename.encode('utf-8')

    g_libtesseract.TessBaseAPISetVariable(
        ctypes.c_void_p(handle),
        b"debug_file",
        filename
    )


def set_page_seg_mode(handle, mode):
    assert(g_libtesseract)

    g_libtesseract.TessBaseAPISetPageSegMode(
        ctypes.c_void_p(handle), ctypes.c_int(mode)
    )


def init_for_analyse_page(handle):
    assert(g_libtesseract)

    g_libtesseract.TessBaseAPIInitForAnalysePage(ctypes.c_void_p(handle))


def set_image(handle, image):
    assert(g_libtesseract)

    image = image.convert("RGB")
    image.load()
    imgdata = image.tobytes("raw", "RGB")

    imgsize = image.size

    g_libtesseract.TessBaseAPISetImage(
        ctypes.c_void_p(handle),
        imgdata,
        ctypes.c_int(imgsize[0]),
        ctypes.c_int(imgsize[1]),
        ctypes.c_int(3),  # RGB = 3 * 8
        ctypes.c_int(imgsize[0] * 3)
    )


def recognize(handle):
    assert(g_libtesseract)

    return g_libtesseract.TessBaseAPIRecognize(
        ctypes.c_void_p(handle), ctypes.c_void_p(None)
    )


def analyse_layout(handle):
    assert(g_libtesseract)

    return g_libtesseract.TessBaseAPIAnalyseLayout(ctypes.c_void_p(handle))


def get_utf8_text(handle):
    assert(g_libtesseract)
    ptr = g_libtesseract.TessBaseAPIGetUTF8Text(ctypes.c_void_p(handle))
    val = ctypes.cast(ptr, ctypes.c_char_p).value.decode("utf-8")
    g_libtesseract.TessDeleteText(ptr)
    return val


def page_iterator_delete(iterator):
    assert(g_libtesseract)

    return g_libtesseract.TessPageIteratorDelete(ctypes.c_void_p(iterator))


def page_iterator_next(iterator, level):
    assert(g_libtesseract)

    return g_libtesseract.TessPageIteratorNext(ctypes.c_void_p(iterator), level)


def page_iterator_is_at_beginning_of(iterator, level):
    assert(g_libtesseract)

    return g_libtesseract.TessPageIteratorIsAtBeginningOf(
        ctypes.c_void_p(iterator), level
    )


def page_iterator_is_at_final_element(iterator, level, element):
    assert(g_libtesseract)

    return g_libtesseract.TessPageIteratorIsAtFinalElement(
        ctypes.c_void_p(iterator), level, element
    )


def page_iterator_block_type(iterator):
    assert(g_libtesseract)

    return g_libtesseract.TessPageIteratorBlockType(
        ctypes.c_void_p(iterator)
    )


def page_iterator_bounding_box(iterator, level):
    assert(g_libtesseract)

    left = ctypes.c_int(0)
    left_p = ctypes.pointer(left)
    top = ctypes.c_int(0)
    top_p = ctypes.pointer(top)
    right = ctypes.c_int(0)
    right_p = ctypes.pointer(right)
    bottom = ctypes.c_int(0)
    bottom_p = ctypes.pointer(bottom)

    r = g_libtesseract.TessPageIteratorBoundingBox(
        ctypes.c_void_p(iterator),
        level,
        left_p,
        top_p,
        right_p,
        bottom_p
    )
    if not r:
        return (False, (0, 0, 0, 0))
    return (True, (left.value, top.value, right.value, bottom.value))


def page_iterator_orientation(iterator):
    assert(g_libtesseract)

    orientation = ctypes.c_int(0)
    writing_direction = ctypes.c_int(0)
    textline_order = ctypes.c_int(0)
    deskew_angle = ctypes.c_float(0.0)

    g_libtesseract.TessPageIteratorOrientation(
        ctypes.c_void_p(iterator),
        ctypes.pointer(orientation),
        ctypes.pointer(writing_direction),
        ctypes.pointer(textline_order),
        ctypes.pointer(deskew_angle)
    )

    return {
        "orientation": orientation.value,
        "writing_direction": writing_direction.value,
        "textline_order": textline_order.value,
        "deskew_angle": deskew_angle.value,
    }


def get_iterator(handle):
    assert(g_libtesseract)

    i = g_libtesseract.TessBaseAPIGetIterator(ctypes.c_void_p(handle))
    return i


def result_iterator_get_page_iterator(res_iterator):
    assert(g_libtesseract)

    return g_libtesseract.TessResultIteratorGetPageIterator(
        ctypes.c_void_p(res_iterator)
    )


def result_iterator_get_utf8_text(iterator, level):
    assert(g_libtesseract)
    ptr = g_libtesseract.TessResultIteratorGetUTF8Text(
        ctypes.c_void_p(iterator), level
    )
    if ptr is None:
        return None
    val = ctypes.cast(ptr, ctypes.c_char_p).value.decode("utf-8")
    g_libtesseract.TessDeleteText(ptr)
    return val


def result_iterator_get_confidence(iterator, level):
    assert(g_libtesseract)
    ptr = g_libtesseract.TessResultIteratorConfidence(
        ctypes.c_void_p(iterator), level
    )
    if ptr is None:
        return None
    val = ctypes.c_float(ptr).value
    return val


def detect_os(handle):
    assert(g_libtesseract)

    # Use the new API function if it is available, because since Tesseract
    # 3.05.00 the old API function _always_ returns False.
    if hasattr(g_libtesseract, 'TessBaseAPIDetectOrientationScript'):
        orientation_deg = ctypes.c_int(0)
        orientation_confidence = ctypes.c_float(0.0)

        r = g_libtesseract.TessBaseAPIDetectOrientationScript(
            ctypes.c_void_p(handle),
            ctypes.byref(orientation_deg),
            ctypes.byref(orientation_confidence),
            None,  # script_name
            None  # script_confidence
        )

        if not r:
            raise TesseractError("detect_orientation failed",
                                 "TessBaseAPIDetectOrientationScript() failed")
        return {
            "orientation": round(orientation_deg.value / 90),
            "confidence": orientation_confidence.value,
        }
    else:  # old API (before Tesseract 3.05.00)
        results = OSResults()
        r = g_libtesseract.TessBaseAPIDetectOS(
            ctypes.c_void_p(handle),
            ctypes.pointer(results)
        )
        if not r:
            raise TesseractError("detect_orientation failed",
                                 "TessBaseAPIDetectOS() failed")
        return {
            "orientation": results.best_orientation_id,
            "confidence": results.best_oconfidence,
        }


def set_input_name(handle, input_file):
    assert(g_libtesseract)

    g_libtesseract.TessBaseAPISetInputName(
        ctypes.c_void_p(handle),
        input_file.encode()
    )


def init_pdf_renderer(handle, output_file, textonly):
    assert(g_libtesseract)

    tessdata_dir = g_libtesseract.TessBaseAPIGetDatapath(handle)

    renderer = g_libtesseract.TessPDFRendererCreate(
        output_file.encode(),
        tessdata_dir,
        ctypes.c_bool(textonly)
    )

    return renderer


def begin_document(renderer, doc_name):
    assert(g_libtesseract)

    g_libtesseract.TessResultRendererBeginDocument(
        ctypes.c_void_p(renderer),
        doc_name.encode()
    )


def add_renderer_image(handle, renderer):
    assert(g_libtesseract)

    g_libtesseract.TessResultRendererAddImage(
        ctypes.c_void_p(renderer),
        ctypes.c_void_p(handle)
    )


def end_document(renderer):
    assert(g_libtesseract)

    g_libtesseract.TessResultRendererEndDocument(
        ctypes.c_void_p(renderer)
    )
