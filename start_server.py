"""WinSpec server start script

Run this script on the spectrometer computer to start the server.

Usage: python start_server <ip_address> <port>

John Jarman <jcj27@cam.ac.uk>
"""
import winspec
import logging
import sys
import winspec.server
import secrets

logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

logger.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Load client authentication token from file or generate new one
try:
    with open('token.txt') as f:
        logging.info('Client token loaded from token.txt')
        token = f.readline()

except FileNotFoundError:
    logging.warning('No client token found, generating a new one')
    with open('token.txt', 'w') as f:
        token = secrets.token_hex()
        f.write(token)
        logging.info('Client token written to token.txt')


# Start server
try:
    winspec.server.WinspecServer(token, *sys.argv[1:]).run()

except KeyboardInterrupt:
    pass

finally:
    logging.info('Server closed')
    