
"""
WinSpec communication class

John Jarman <jcj27@cam.ac.uk>
"""

import logging
import threading
import time
import numpy as np
from winspec.exceptions import WinspecError, WinspecErrorCodes

import comtypes.client
import win32com.client as win32
import ctypes

comtypes.client.GetModule(('{1A762221-D8BA-11CF-AFC2-508201C10000}', 3, 11))
import comtypes.gen.WINX32Lib as WinSpecLib

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
            wx32_expt = win32.Dispatch("WinX32.ExpSetup")
            wx32_doc = win32.Dispatch("WinX32.DocFile")
            wx32_expt.Start(wx32_doc)

            while wx32_expt.GetParam(WinSpecLib.EXP_RUNNING)[0]:
                time.sleep(1)

            raw_spectrum_buffer = ctypes.c_uint16()

            wx32_doc.GetFrame(1, raw_spectrum_buffer)

            raw_spectrum = np.ctypeslib.as_array(raw_spectrum_buffer)
            
            spectrum = np.empty((2, len(raw_spectrum)))
            spectrum[1] = spectrum
            calibration = wx32_doc.GetCalibration()
            
            poly_coeffs = np.array([])

            for i in range(calibration.Order + 1):
                np.insert(poly_coeffs, 0, calibration.PolyCoeffs(i))

            spectrum[0] = np.polyval(poly_coeffs, range(1, 1+len(raw_spectrum)))
            
            logging.info('Acquire complete')
            return spectrum
        
        finally:
            self._lock.release()