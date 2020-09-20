"""Demo for how to use the Winspec client class to talk to a Winspec server

The WinspecClient class should be used with a context manager (the `with`
statement) to ensure it is connected and disconnected properly.

Spectrometer parameters can be accessed with `get_parameter('<param_name>')`

Spectrometer parameters can be set using `set_parameters(<param_name>=<param_val>)`

Trigger an acquisition and get the resulting spectrum using `acquire()`.

Parameters are 'wavelength' (in nanometres) and 'exposure_time' (in seconds)

John Jarman <jcj27@cam.ac.uk>
"""

import winspec

server_address = 'ws://localhost:1234'

# Copy this from token.txt on the server PC, in the winspec-server directory
token = '27bdb9304ba259abc6b41d86dbdecc8b8c08d68537c8d970555eb4e2658d05f0'

with winspec.WinspecClient(server_address, token) as ws_client:
    ws_client.set_parameters(wavelength=650, exposure_time=10)
    exp_time = ws_client.get_parameter('exposure_time')
    spectrum = ws_client.acquire()

# spectrum[0] contains the wavelength axis
# spectrum[1] contains the intensity axis
