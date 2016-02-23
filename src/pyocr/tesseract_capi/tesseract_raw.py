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
        ctypes.c_void_p  # TessBaseAPI*
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


def _init(lang=None):
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


def _cleanup(handle):
    g_libtesseract.TessBaseAPIDelete(handle)


def is_available():
    global g_libtesseract
    return g_libtesseract is not None


def get_version():
    global g_libtesseract
    return g_libtesseract.TessVersion().decode("utf-8")


def get_available_languages():
    global g_libtesseract
    langs = []
    handle = _init()
    try:
        c_langs = g_libtesseract.TessBaseAPIGetAvailableLanguagesAsVector(
            handle
        )
        i = 0
        while c_langs[i]:
            langs.append(c_langs[i].decode("utf-8"))
            i += 1
    finally:
        _cleanup(handle)
    return langs
