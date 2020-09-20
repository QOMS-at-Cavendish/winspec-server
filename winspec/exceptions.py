"""Exception for Winspec-related errors

Uses an error number to allow errors to be communicated over the websocket and
re-raised on the client side.

John Jarman <jcj27@cam.ac.uk>
"""
import enum

class WinspecErrorCodes(enum.IntEnum):
    UnknownError = -1

    # Hardware-related errors
    SpectrometerBusy = 1
    OutOfRange = 2
    HardwareError = 3
    ParameterError = 4

    # Server-related errors
    JSONDecodeError = 101
    UnrecognisedVariable = 102
    UnrecognisedCommand = 103
    AuthenticationError = 104

class WinspecError(Exception):
    """Class for hardware and server errors.

    Args:
        err (int): winspec.WinspecErrorCodes error code
        errmsg (str): Supplementary error message

    Attributes:
        errno (int): Error code (see `WinspecErrorCodes`)
        msg (str): Supplementary error message
    """
    def __init__(self, errno=-1, msg=''):
        super().__init__(self)
        self.msg = msg
        self.errno = WinspecErrorCodes(errno)
    
    def __repr__(self):
        return "E{} {}: {}".format(self.errno, self.errno.name, self.msg)

    def __str__(self):
        return self.__repr__()
