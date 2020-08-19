
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
#pylint: disable=no-name-in-module, import-error
import comtypes.gen.WINX32Lib as WinSpecLib

class WinspecCOM:
    """
    Class for communication with WinSpec using COM

    """
    def __init__(self):
        self._lock = threading.Lock()

    def set_wavelength(self, wavelength):
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
        #pylint: disable=no-member
        win32.pythoncom.CoInitialize()
        spectrograph = self._get_spectrograph()
        return spectrograph.GetParam(WinSpecLib.SPT_CUR_POSITION, 0)[0]
        
    def set_exposure_time(self, exp_time):
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
        #pylint: disable=no-member
        win32.pythoncom.CoInitialize()
        wx32_expt = win32.Dispatch("WinX32.ExpSetup")
        return wx32_expt.GetParam(WinSpecLib.EXP_EXPOSURE)[0]

    def acquire_spectrum(self):
        if not self._lock.acquire(blocking=False):
            raise WinspecError(WinspecErrorCodes.SpectrometerBusy,
                               'Unable to start acquisition due to concurrent operation')
        try:
            logging.info('Acquire spectrum')
            #pylint: disable=no-member
            win32.pythoncom.CoInitialize()
            wx32_expt = win32.Dispatch("WinX32.ExpSetup")
            wx32_doc = win32.Dispatch("WinX32.DocFile")
            
            retval = wx32_expt.Start(wx32_doc)
            
            if retval != 0:
                self._raise_hw_error(retval)

            while True:
                done, status = wx32_expt.GetParam(WinSpecLib.EXP_RUNNING)
                if status != 0:
                    self._raise_hw_error(status)
                if done:
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

            return [wavelength, intensity]
        
        finally:
            self._lock.release()
        
    def _get_spectrograph(self):
        spectro_obj_mgr = win32.Dispatch("WinX32.SpectroObjMgr")
        return spectro_obj_mgr.Current
        
    def _raise_hw_error(self, retval='unknown'):
        raise WinspecError(WinspecErrorCodes.HardwareError,
                           'Spectrometer error {}'.format(retval))