"""
Demo for how to use the Winspec client class to talk to a Winspec server

John Jarman <jcj27@cam.ac.uk>
"""

import winspec.client
import time

with winspec.client.WinspecClient('ws://localhost:1234') as ws_client:
    ws_client.set_wavelength(500)
