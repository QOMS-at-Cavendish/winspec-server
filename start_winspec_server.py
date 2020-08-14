"""
WinSpec server start script

Run this script on the spectrometer computer to start the server.

John Jarman <jcj27@cam.ac.uk>
"""
import winspec.server
import asyncio
import logging
import sys

logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

logger.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Start server
try:
    asyncio.run(winspec.server.WinspecServer().run())

except KeyboardInterrupt:
    pass

finally:
    logging.info('Server closed')
    