"""
Websockets server for controlling WinSpec over the network

John Jarman <jcj27@cam.ac.uk>
"""
import asyncio
import concurrent.futures
import logging
import websockets
import json
from winspec import winspec_com

class WinspecServer:
    """
    WinspecServer main class

    Usage:
    ws = WinspecServer(ip, port)
    asyncio.run(ws.run())
    """

    def __init__(self, ip='localhost', port=1234):
        self.connections = set()
        self.ip = ip
        self.port = port
        self.shutdown_request = False

        self.winspec = winspec_com.WinspecCOM()

        self.winspec_vars = [
            {'name':'wavelength',
            'getter':self.winspec.get_wavelength,
            'setter':self.winspec.set_wavelength}
        ]

    async def run(self):
        """
        Run websocket server.
        
        Call using asyncio.run()

        Returns when server shuts down.
        """
        server = await websockets.serve(self._serve, self.ip, self.port)
        logging.info('Server started at {}:{}'.format(self.ip, self.port))
        await server.wait_closed()
        logging.info('Server shutdown')

    async def _serve(self, websocket, path):
        """
        Handle incoming connections
        """
        try:
            self.connections.add(websocket)
            remote_ip = websocket.remote_address[0]
            logging.info('Client connected from {}'.format(remote_ip))
            async for command in websocket:
                # Decode and handle incoming commands
                try:
                    cmd = json.loads(command)
                    await self._handle_command(cmd, websocket)
                except json.JSONDecodeError as err:
                    logging.error('JSONDecodeError')
                    await websocket.send(json.dumps({'error':'JSONDecodeError',
                                                    'errormsg':str(err)}))

        except websockets.ConnectionClosed:
            logging.info('Client disconnected from {}'.format(remote_ip))

        finally:
            self.connections.discard(websocket)

    async def _handle_command(self, command, websocket):
        """
        Handle commands from connected clients

        Format: {'cmd':<command>, '<variable_name>':<value>, ...}

        'cmd' is one of: 'set', 'get' or 'acquire'
            - 'set': set variables
            - 'get': request value of specified variables
            - 'acquire': trigger acquisition
        """
        if command['cmd'] == 'set':
            # Set and read back variables
            keys = command.keys()
            completed_settings = dict()
            try:
                for var in self.winspec_vars:
                    if var['name'] in keys:
                        loop = asyncio.get_running_loop()
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            await loop.run_in_executor(executor, var['setter'], command[var['name']])
                            completed_settings[var['name']] = await loop.run_in_executor(executor, var['getter'])

            except winspec_com.WinspecError as err:
                await websocket.send(json.dumps({'error':'WinspecError', 'errormsg':str(err)}))

            finally:
                await websocket.send(json.dumps({'complete':True, **completed_settings}))
