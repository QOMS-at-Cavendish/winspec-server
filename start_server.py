"""WinSpec server start script

Run this script on the spectrometer computer to start the server.

Usage: python start_server <ip_address> <port>

John Jarman <jcj27@cam.ac.uk>
"""
import winspec
import asyncio
import logging
import sys
import winspec.server

logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

logger.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Start server
try:
    asyncio.run(winspec.server.WinspecServer(*sys.argv[1:]).run())

except KeyboardInterrupt:
    pass

finally:
    logging.info('Server closed')
    