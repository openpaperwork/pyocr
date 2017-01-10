class PyocrException(Exception):
    pass


class TesseractError(PyocrException):
    """
    Obsolete. You should look for PyocrException
    """
    def __init__(self, status, message):
        PyocrException.__init__(self, message)
        self.status = status
        self.message = message
        self.args = (status, message)
