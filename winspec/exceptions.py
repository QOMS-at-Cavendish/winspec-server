"""
Exception class for Winspec-related errors

John Jarman <jcj27@cam.ac.uk>
"""
import enum

class WinspecErrorCodes(enum.IntEnum):
    UnknownError = -1

    # Hardware-related errors
    SpectrometerBusy = 1
    OutOfRange = 2

    # Server-related errors
    JSONDecodeError = 101
    UnrecognisedVariable = 102

class WinspecError(Exception):
    def __init__(self, errno=-1, msg=''):
        super().__init__(self)
        self.msg = msg
        self.errno = WinspecErrorCodes(errno)
    
    def __repr__(self):
        return "E{} {}: {}".format(self.errno, self.errno.name, self.msg)

    def __str__(self):
        return self.__repr__()

    