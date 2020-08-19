
"""WinSpec COM communication class

Communicate with Winspec32 via COM/OLE/ActiveX

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
#pylint: disable=no-name-in-module, import-error
import comtypes.gen.WINX32Lib as WinSpecLib

class WinspecCOM:
    """Communicate with WinSpec using COM

    All methods block until the required operation is completed. Methods are 
    thread-safe and raise an exception if a conflicting operation is attempted.
    """

    def __init__(self):
        self._lock = threading.Lock()

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
            #pylint: disable=no-member
            win32.pythoncom.CoInitialize()
            spectrograph = self._get_spectrograph()
            
            retval = spectrograph.SetParam(WinSpecLib.SPT_NEW_POSITION, float(wavelength))
            
            if retval == WinSpecLib.WRONG_WAVELENGTH:
                raise WinspecError(WinspecErrorCodes.OutOfRange,
                                   'Wavelength out of range')
            elif retval != 0:
                self._raise_hw_error(retval)
            
            retval = spectrograph.Move()
            
            if retval != 0:
                self._raise_hw_error(retval)
            
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
        #pylint: disable=no-member
        win32.pythoncom.CoInitialize()
        spectrograph = self._get_spectrograph()
        return spectrograph.GetParam(WinSpecLib.SPT_CUR_POSITION, 0)[0]
        
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
            #pylint: disable=no-member
            win32.pythoncom.CoInitialize()
            wx32_expt = win32.Dispatch("WinX32.ExpSetup")
            
            retval = wx32_expt.SetParam(WinSpecLib.EXP_EXPOSURE, float(exp_time))
            
            if retval != 0:
                self._raise_hw_error(retval)
            
        finally:
            self._lock.release()
            
    def get_exposure_time(self):
        """Get exposure time

        Returns:
            float: Exposure time in seconds.
        """
        #pylint: disable=no-member
        win32.pythoncom.CoInitialize()
        wx32_expt = win32.Dispatch("WinX32.ExpSetup")
        return wx32_expt.GetParam(WinSpecLib.EXP_EXPOSURE)[0]

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
            #pylint: disable=no-member
            win32.pythoncom.CoInitialize()
            wx32_expt = win32.Dispatch("WinX32.ExpSetup")
            wx32_doc = win32.Dispatch("WinX32.DocFile")
            
            retval = wx32_expt.Start(wx32_doc)[0]
            
            if retval != True:
                self._raise_hw_error(retval)

            while True:
                running, status = wx32_expt.GetParam(WinSpecLib.EXP_RUNNING)
                if status != 0:
                    self._raise_hw_error(status)
                if not running:
                    break
                time.sleep(0.1)

            ptr = ctypes.POINTER(ctypes.c_float)

            raw_spectrum_buffer = wx32_doc.GetFrame(1, ptr)

            intensity = np.array(raw_spectrum_buffer, dtype=np.uint16).flatten()

            calibration = wx32_doc.GetCalibration()
            
            poly_coeffs = np.zeros(calibration.Order + 1)

            for i in range(calibration.Order + 1):
                poly_coeffs[i] = calibration.PolyCoeffs(i)

            wavelength = np.polyval(poly_coeffs[::-1], np.arange(1, 1+len(intensity)))

            return [wavelength.tolist(), intensity.tolist()]
        
        finally:
            self._lock.release()
        
    def _get_spectrograph(self):
        """Get current spectrograph object
        
        Returns:
            WinX32.SpectroObj: the current spectrograph object.
        """
        spectro_obj_mgr = win32.Dispatch("WinX32.SpectroObjMgr")
        return spectro_obj_mgr.Current
        
    def _raise_hw_error(self, retval='unknown'):
        """Raise generic WinspecError in response to non-zero return value.

        Args:
            retval (int): The non-zero return value.
        """
        raise WinspecError(WinspecErrorCodes.HardwareError,
                           'Spectrometer error {}'.format(retval))