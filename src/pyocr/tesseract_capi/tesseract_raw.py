import ctypes
import os
import sys

TESSDATA_PREFIX = os.getenv('TESSDATA_PREFIX', "../")

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


def is_available():
    global g_libtesseract
    return g_libtesseract is not None


def get_version():
    global g_libtesseract
    return g_libtesseract.TessVersion().decode("utf-8")
