import ctypes

class ProcName(object):
    def __init__(self):
        return

    @staticmethod
    def set(new_title):
        # Change name process
        lib = ctypes.cdll.LoadLibrary(None)
        prctl = lib.prctl
        prctl.restype = ctypes.c_int
        prctl.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_ulong,
                          ctypes.c_ulong, ctypes.c_ulong]
        result = prctl(15, new_title, 0, 0, 0)
        if result != 0:
            raise OSError("prctl result: %d" % result)
