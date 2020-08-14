
"""
WinSpec communication class

John Jarman <jcj27@cam.ac.uk>
"""

import logging
import threading
import time
from winspec.exceptions import WinspecError

class WinspecCOM:
    """
    Class for communication with WinSpec using COM

    """
    def __init__(self):
        logging.info('Initialised WinspecCOM')
        self.wavelength = 0
        self._lock = threading.Lock()

    def set_wavelength(self, wavelength):
        if not self._lock.acquire(blocking=False):
            raise WinspecError('Unable to update wavelength due to concurrent operation', True)

        logging.info('Set wavelength {}'.format(wavelength))
        for i in range(5):
            time.sleep(1)
        self.wavelength = wavelength
        self._lock.release()
    
    def get_wavelength(self):
        return self.wavelength
