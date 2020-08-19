# Winspec remote access server

A server and client to allow remote control of the Winspec spectrometers in Python.

## Requirements

This code is based on the `websockets` module, which needs at least Python 3.4.

## Installation

1. Download the code
2. Run `python setup.py install` from the code directory
3. Access the module using `import winspec` in your scripts

See `examples/client_demo.py` for sample code that shows the client-side API.

## Server-side setup

1. Run the installation as above, then also install the `pywin32` and `comtypes`
packages using `pip`.

2. Ensure Winspec is open.

3. Run `python start_server.py <ip_address>` on the spectrometer PC, replacing 
`<ip_address>` with the IP of the spectrometer PC.

4. The server has no security or authentication built in, so edit the Python
rules in Windows Firewall, changing the scope to only include the IP addresses
or address range used by the lab PCs.

If Winspec is running as administrator, you will need to execute Python from
a console that also has administrator privileges.