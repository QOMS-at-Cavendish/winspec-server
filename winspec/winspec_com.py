
"""
WinSpec communication class

John Jarman <jcj27@cam.ac.uk>
"""

import logging
import threading
import time
from winspec.exceptions import WinspecError, WinspecErrorCodes

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
            raise WinspecError(WinspecErrorCodes.SpectrometerBusy, 
                               'Unable to update wavelength due to concurrent operation')
        try:
            logging.info('Set wavelength {}'.format(wavelength))
            time.sleep(1)
            self.wavelength = wavelength
        finally:
            self._lock.release()
    
    def get_wavelength(self):
        return self.wavelength

    def acquire_spectrum(self):
        if not self._lock.acquire(blocking=False):
            raise WinspecError(WinspecErrorCodes.SpectrometerBusy,
                               'Unable to start acquisition due to concurrent operation')
        try:
            logging.info('Acquire spectrum')
            time.sleep(25)
            logging.info('Acquire complete')
        finally:
            self._lock.release()