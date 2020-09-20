
"""Dummy winspec module

Used for testing away from the spectrometer

John Jarman <jcj27@cam.ac.uk>
"""

import logging
import threading
import time
import numpy as np
from winspec.exceptions import WinspecError, WinspecErrorCodes

import tempfile

class WinspecCOM:
    """Communicate with WinSpec using COM

    All methods block until the required operation is completed. Methods are 
    thread-safe and raise an exception if a conflicting operation is attempted.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.wavelength = 500
        self.det_temp = -100
        self.exposure = 10

    def set_wavelength(self, wavelength):
        """Set wavelength

        Moves grating to change central wavelength of spectrograph.

        Args:
            wavelength (float): Wavelength to set in nanometres.

        Raises:
            winspec.WinspecError for hardware problems.
        """
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
        """Get wavelength.

        This returns the currently set wavelength of the spectrograph. The value
        is read from the Winspec software, which just reports its internally stored
        value, so in some cases this may not reflect the actual position of the grating.

        Returns:
            wavelength (float): The currently set wavelength in nanometres
        """
        return self.wavelength
        
    def set_exposure_time(self, exp_time):
        """Set exposure time.

        Args:
            exp_time (float): Exposure time in seconds.
        
        Raises:
            winspec.WinspecError for hardware problems.
        """
        if not self._lock.acquire(blocking=False):
            raise WinspecError(WinspecErrorCodes.SpectrometerBusy, 
                               'Unable to update wavelength due to concurrent operation')
        try:
            logging.info('Set exposure time {}'.format(exp_time))
            time.sleep(1)
            self.exposure = exp_time
            
        finally:
            self._lock.release()
            
    def get_exposure_time(self):
        """Get exposure time

        Returns:
            float: Exposure time in seconds.
        """
        return self.exposure

    def get_detector_temp(self):
        return self.det_temp

    def acquire_spectrum(self):
        """Acquire spectrum.

        Returns::
            [wavelength[], intensity[]]
        """
        if not self._lock.acquire(blocking=False):
            raise WinspecError(WinspecErrorCodes.SpectrometerBusy,
                               'Unable to start acquisition due to concurrent operation')
        try:
            logging.info('Acquire spectrum')
            time.sleep(self.exposure)
            return [[0, 1, 2], [3, 4, 5]]

        finally:
            self._lock.release()
        
    def _raise_hw_error(self, retval='unknown'):
        """Raise generic WinspecError in response to non-zero return value.

        Args:
            retval (int): The non-zero return value.
        """
        raise WinspecError(WinspecErrorCodes.HardwareError,
                           'Spectrometer error {}'.format(retval))