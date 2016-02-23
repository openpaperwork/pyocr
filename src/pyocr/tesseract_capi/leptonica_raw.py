import ctypes

# TODO(Jflesch): win32/win64 ?
libnames = [
    "liblept.so.4",
]


g_liblept = None

for libname in libnames:
    try:
        g_liblept = ctypes.cdll.LoadLibrary(libname)
    except OSError:
        pass

if g_liblept:
    # TODO
    pass


def is_available():
    global g_liblept
    return g_liblept is not None
