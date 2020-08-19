"""Demo for how to use the Winspec client class to talk to a Winspec server

The WinspecClient class should be used with a context manager (the `with`
statement) to ensure it is connected and disconnected properly.

Spectrometer parameters can be accessed with `get_parameter('<param_name>')`

Spectrometer parameters can be set using `set_parameters(<param_name>=<param_val>)`

Trigger an acquisition and get the resulting spectrum using `acquire()`.

Parameters are 'wavelength' (in nanometres) and 'exp_time' (in seconds)

John Jarman <jcj27@cam.ac.uk>
"""

import winspec

with winspec.WinspecClient('ws://localhost:1234') as ws_client:
    ws_client.set_parameters(wavelength=650, exp_time=10)
    spectrum = ws_client.acquire()

# spectrum[0] contains the wavelength axis
# spectrum[1] contains the intensity axis
