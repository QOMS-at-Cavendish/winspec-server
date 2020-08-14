"""
Exception class for Winspec-related errors

John Jarman <jcj27@cam.ac.uk>
"""

import logging

class WinspecError(Exception):
    def __init__(self, msg='', log=False):
        super().__init__(self)
        self.msg = msg
        if log:
            logging.error('{}'.format(msg))
    
    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.msg