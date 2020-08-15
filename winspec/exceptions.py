"""
Exception class for Winspec-related errors

John Jarman <jcj27@cam.ac.uk>
"""

class WinspecError(Exception):
    def __init__(self, msg=''):
        super().__init__(self)
        self.msg = msg
    
    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.msg