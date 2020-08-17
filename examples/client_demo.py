"""
Demo for how to use the Winspec client class to talk to a Winspec server

John Jarman <jcj27@cam.ac.uk>
"""

import winspec

with winspec.WinspecClient('ws://localhost:1234') as ws_client:
    ws_client.set_parameters(wavelength=500)
    ws_client.acquire()